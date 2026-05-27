import json
import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from backend import ai_engine, game_logic, database
from backend.models import (
    GameState, NewGameRequest, DiplomacyAction, IssueResponse,
    DeclareWarRequest, War, WarFront, ResourceTradeOffer,
    ResourceTradeRequest, TroopRequest, TechPurchaseRequest,
    JointResearchRequest, AllianceUpgradeRequest,
    ArmyDivision, CreateArmyRequest, AssignArmyRequest, ConscriptionRequest,
)
from backend.army_templates import get_template, all_templates, get_conscription_law, all_conscription_laws

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

# In-memory game sessions (game_id -> GameState)
_sessions: dict[str, GameState] = {}
# Active WebSocket connections (game_id -> list of WebSocket)
_ws_connections: dict[str, list[WebSocket]] = {}
_clock_tasks: dict[str, asyncio.Task] = {}
_clock_locks: dict[str, asyncio.Lock] = {}
_game_speeds: dict[str, float] = {}   # game_id -> speed multiplier (0=paused, 1=normal, 2=2x, 3=3x)
SECONDS_PER_MONTH = 120


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.init_db()
    yield


app = FastAPI(title="Grand Strategy AI", lifespan=lifespan)


async def _broadcast(game_id: str, message: dict):
    sockets = _ws_connections.get(game_id, [])
    dead = []
    for ws in sockets:
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        sockets.remove(ws)


async def _get_state(game_id: str) -> GameState:
    if game_id in _sessions:
        return _sessions[game_id]
    state = await database.load_game(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Game not found")
    _sessions[game_id] = state
    return state


async def _save_state(state: GameState):
    _sessions[state.game_id] = state
    await database.save_game(state)


async def _run_game_clock(game_id: str):
    lock = _clock_locks.setdefault(game_id, asyncio.Lock())
    while True:
        speed = _game_speeds.get(game_id, 1.0)
        if speed == 0:
            await asyncio.sleep(2)   # poll while paused
            continue
        sleep_time = SECONDS_PER_MONTH / max(speed, 0.1)
        await asyncio.sleep(sleep_time)
        async with lock:
            if game_id not in _sessions:
                return
            # Re-check speed after sleep (may have been paused)
            if _game_speeds.get(game_id, 1.0) == 0:
                continue
            try:
                state = await _get_state(game_id)
                state, _ = await game_logic.process_full_turn(state, broadcast_fn=None)
                await _save_state(state)
                await _broadcast(game_id, {"type": "state_update", "state": state.model_dump()})
            except Exception as e:
                print(f"Clock tick failed for {game_id}: {e}")


def _load_eras() -> dict:
    with open(os.path.join(DATA_DIR, "eras.json")) as f:
        data = json.load(f)
    return {e["id"]: e for e in data["eras"]}


# ── API Routes ──────────────────────────────────────────────────────────────


@app.get("/api/status")
async def get_status():
    ai_status = await ai_engine.check_ai_server()
    return {"game": "online", "ai": ai_status}


@app.get("/api/eras")
async def get_eras():
    with open(os.path.join(DATA_DIR, "eras.json")) as f:
        return json.load(f)


@app.get("/api/saves")
async def list_saves():
    return await database.list_saves()


@app.post("/api/game/new")
async def new_game(request: NewGameRequest):
    eras = _load_eras()
    era = eras.get(request.era_id)
    if not era:
        raise HTTPException(status_code=400, detail="Unknown era")

    # Build the fallback world instantly (pure Python, no AI) — <1 second
    state = game_logic.initialize_game_instant(
        request.era_id, era, request.player_nation_name, request.ideology
    )

    # Grab starter issues from pool (instant fallbacks, no AI)
    from backend.models import Issue, IssueOption
    await database.seed_pool_if_empty([
        {**issue, "issue_type": itype}
        for itype, issues in ai_engine._ISSUES.items()
        for issue in issues
    ])
    for itype in ["economic", "political"]:
        pool_issue = await database.get_pool_issue(issue_type=itype)
        if pool_issue:
            await database.mark_pool_issue_used(pool_issue["id"])
            opts = [
                IssueOption(id=o["id"], text=o["text"], effects=o.get("effects", {}), flavor=o.get("flavor", ""))
                for o in pool_issue.get("options", [])
            ]
            if opts:
                state.pending_issues.append(Issue(
                    title=pool_issue["title"],
                    description=pool_issue.get("description", ""),
                    issue_type=pool_issue.get("issue_type", itype),
                    urgency=pool_issue.get("urgency", "normal"),
                    options=opts,
                ))

    await _save_state(state)

    # Fire AI world gen in background — updates map via WebSocket when ready
    asyncio.create_task(_bg_world_gen(state.game_id, request.era_id, era,
                                      request.player_nation_name, request.ideology))

    # Start real-time game clock
    if state.game_id not in _clock_tasks:
        _clock_tasks[state.game_id] = asyncio.create_task(_run_game_clock(state.game_id))

    return {"game_id": state.game_id, "player_nation": state.player_nation_id, "world_ready": False}


async def _bg_world_gen(game_id: str, era_id: str, era: dict, player_nation: str, ideology: str):
    """Background: run AI world gen, update live state, notify frontend via WebSocket."""
    try:
        state = _sessions.get(game_id)
        if not state:
            state = await database.load_game(game_id)
        if not state:
            return

        state = await game_logic.run_ai_world_gen(state, era_id, era, player_nation, ideology)
        _sessions[game_id] = state
        await database.save_game(state)
        print(f"AI world gen complete for {game_id}: {len(state.nations)} nations")

        # Notify the frontend — it will refresh the full game state
        await _broadcast(game_id, {"type": "world_ready", "state": state.model_dump()})

        # Now seed starter content (low priority, after world gen)
        asyncio.create_task(game_logic._seed_starter_content(
            era["name"], ideology, state.year, state
        ))
    except Exception as e:
        print(f"Background world gen failed: {e}")
        # Notify frontend that world gen failed (fallback world remains)
        await _broadcast(game_id, {"type": "world_ready", "state": None, "error": str(e)})


@app.get("/api/game/{game_id}")
async def get_game_state(game_id: str):
    state = await _get_state(game_id)
    # Restart the real-time clock if it died (e.g. after server restart / save load)
    if state.game_id not in _clock_tasks or _clock_tasks[state.game_id].done():
        _clock_tasks[state.game_id] = asyncio.create_task(_run_game_clock(state.game_id))
    return state.model_dump()


@app.post("/api/game/{game_id}/save")
async def manual_save(game_id: str):
    state = await _get_state(game_id)
    await database.save_game(state)
    return {"message": "Game saved.", "turn": state.turn, "year": state.year, "month": state.month}


@app.post("/api/game/{game_id}/speed")
async def set_game_speed(game_id: str, body: dict):
    """Set the real-time game speed. 0=paused, 1=normal, 2=double, 3=triple."""
    speed = float(body.get("speed", 1.0))
    if speed not in (0, 1, 2, 3):
        raise HTTPException(status_code=400, detail="speed must be 0, 1, 2, or 3")
    _game_speeds[game_id] = speed
    # Ensure clock task is running
    if game_id not in _clock_tasks or _clock_tasks[game_id].done():
        _clock_tasks[game_id] = asyncio.create_task(_run_game_clock(game_id))
    return {"speed": speed, "paused": speed == 0}


@app.delete("/api/game/{game_id}")
async def delete_game(game_id: str):
    _sessions.pop(game_id, None)
    task = _clock_tasks.pop(game_id, None)
    if task:
        task.cancel()
    await database.delete_save(game_id)
    return {"deleted": game_id}


@app.post("/api/game/{game_id}/turn")
async def advance_turn(game_id: str):
    state = await _get_state(game_id)

    # Check unresolved mandatory issues
    unresolved = [i for i in state.pending_issues if not i.resolved and i.urgency == "critical"]
    if unresolved:
        return {"error": "Resolve all critical issues before advancing.", "blocked": True}

    await _broadcast(game_id, {"type": "turn_processing", "message": "Processing turn..."})

    async def bcast(msg):
        await _broadcast(game_id, msg)

    state, logs = await game_logic.process_full_turn(state, broadcast_fn=bcast)
    await _save_state(state)
    await _broadcast(game_id, {"type": "turn_complete", "logs": logs, "state": state.model_dump()})

    return {"turn": state.turn, "year": state.year, "month": state.month, "logs": logs}


@app.get("/api/game/{game_id}/issues")
async def get_issues(game_id: str):
    state = await _get_state(game_id)
    return {"issues": [i.model_dump() for i in state.pending_issues if not i.resolved]}


@app.post("/api/game/{game_id}/issue/{issue_id}/respond")
async def respond_to_issue(game_id: str, issue_id: str, response: IssueResponse):
    state = await _get_state(game_id)
    issue = next((i for i in state.pending_issues if i.id == issue_id), None)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    if issue.resolved:
        raise HTTPException(status_code=400, detail="Issue already resolved")

    state, result_text = game_logic.apply_issue_effects(state, issue, response.option_id)
    await _save_state(state)
    await _broadcast(game_id, {"type": "issue_resolved", "issue_id": issue_id, "result": result_text})
    return {"result": result_text, "state": state.model_dump()}


@app.post("/api/game/{game_id}/diplomacy")
async def diplomatic_action(game_id: str, action: DiplomacyAction):
    state = await _get_state(game_id)
    player = state.get_player_nation()
    if not player:
        raise HTTPException(status_code=400, detail="No player nation")

    target_id = game_logic.find_nation_id(state, action.target_nation)
    if not target_id:
        raise HTTPException(status_code=404, detail="Target nation not found")

    target = state.nations[target_id]

    # ── Sanctions are unilateral — do not require target acceptance ──────────
    if action.action_type == "impose_sanctions":
        already_sanctioned = target_id in player.diplomacy.sanctions_against
        if not already_sanctioned:
            player.diplomacy.sanctions_against.append(target_id)
            target.economy.gdp_growth = max(-0.10, target.economy.gdp_growth - 0.012)
            # Sanctions hurt relations both ways
            player.diplomacy.relations[target_id] = max(-100, player.diplomacy.relations.get(target_id, 0) - 15)
            target.diplomacy.relations[state.player_nation_id] = max(-100, target.diplomacy.relations.get(state.player_nation_id, 0) - 20)
            state.add_news(
                f"{player.name} imposes economic sanctions on {target.name}",
                state.player_nation_id, "diplomacy"
            )
            state.nations[state.player_nation_id] = player
            state.nations[target_id] = target
            await _save_state(state)
        return {
            "accepted": True,
            "response_message": (
                f"Sanctions already in effect against {target.name}." if already_sanctioned
                else f"Sanctions imposed on {target.name}. Their economy will suffer."
            ),
            "counteroffer": None,
            "relation_change": -15 if not already_sanctioned else 0,
            "rejection_reason": None,
        }

    if action.action_type == "lift_sanctions":
        if target_id in player.diplomacy.sanctions_against:
            player.diplomacy.sanctions_against.remove(target_id)
            target.economy.gdp_growth = min(0.10, target.economy.gdp_growth + 0.012)
            state.nations[state.player_nation_id] = player
            state.nations[target_id] = target
            await _save_state(state)
        return {
            "accepted": True,
            "response_message": f"Sanctions against {target.name} lifted.",
            "counteroffer": None,
            "relation_change": 5,
            "rejection_reason": None,
        }

    # ── Other actions require diplomatic negotiation ─────────────────────────
    response = await ai_engine.generate_diplomatic_response(
        target.model_dump(), player.model_dump(), action.action_type, action.details
    )

    relation_change = response.get("relation_change", 0)
    current_rel = player.diplomacy.relations.get(target_id, 0)
    player.diplomacy.relations[target_id] = max(-100, min(100, current_rel + relation_change))
    target.diplomacy.relations[state.player_nation_id] = max(-100, min(100, target.diplomacy.relations.get(state.player_nation_id, 0) + relation_change))

    accepted = response.get("accepted", False)

    if accepted:
        if action.action_type == "form_alliance":
            if target_id not in player.diplomacy.alliances:
                player.diplomacy.alliances.append(target_id)
                target.diplomacy.alliances.append(state.player_nation_id)
                state.add_news(f"{player.name} and {target.name} forge an alliance", state.player_nation_id, "diplomacy")

        elif action.action_type == "trade_deal":
            if target_id not in player.diplomacy.trade_deals:
                player.diplomacy.trade_deals.append(target_id)
                target.diplomacy.trade_deals.append(state.player_nation_id)
                player.economy.gdp_growth = min(0.15, player.economy.gdp_growth + 0.005)
                state.add_news(f"{player.name} and {target.name} sign a trade deal", state.player_nation_id, "diplomacy")

        elif action.action_type == "defense_pact":
            if target_id not in player.diplomacy.defense_pacts:
                player.diplomacy.defense_pacts.append(target_id)
                target.diplomacy.defense_pacts.append(state.player_nation_id)
                state.add_news(f"{player.name} and {target.name} sign a defense pact", state.player_nation_id, "diplomacy")

    # Rejection reason for player feedback
    rejection_reason = None
    if not accepted:
        rel = player.diplomacy.relations.get(target_id, 0)
        if rel < -30:
            rejection_reason = "hostile_relations"
        elif action.action_type == "form_alliance":
            rejection_reason = "insufficient_trust"
        elif action.action_type == "trade_deal":
            rejection_reason = "unfavorable_terms"
        else:
            rejection_reason = "political_disagreement"

    state.nations[state.player_nation_id] = player
    state.nations[target_id] = target
    await _save_state(state)

    return {
        "accepted": accepted,
        "response_message": response.get("response_message", ""),
        "counteroffer": response.get("counteroffer"),
        "relation_change": relation_change,
        "rejection_reason": rejection_reason,
    }


@app.post("/api/game/{game_id}/war/declare")
async def declare_war(game_id: str, req: DeclareWarRequest):
    state = await _get_state(game_id)
    player = state.get_player_nation()
    if not player:
        raise HTTPException(status_code=400, detail="No player nation")
    if player.is_at_war:
        raise HTTPException(status_code=400, detail="Already at war")

    target_id = game_logic.find_nation_id(state, req.target_nation)
    if not target_id:
        raise HTTPException(status_code=404, detail="Target nation not found")
    if target_id == state.player_nation_id:
        raise HTTPException(status_code=400, detail="Cannot declare war on yourself")

    target = state.nations[target_id]
    if target.is_at_war:
        raise HTTPException(status_code=400, detail="Target already at war")

    # Ideology-based war gate: democracies need justification or high world tension
    democratic_ideologies = {"Liberal Democracy", "Social Democracy", "Conservative Democracy"}
    defensive_casus = {"defensive_war", "retaliation", "alliance_defense"}
    if player.ideology in democratic_ideologies and req.casus_belli not in defensive_casus:
        if state.world_tension < 0.40:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Your democratic parliament refuses to authorize an unprovoked war. "
                    f"World tension must reach 40% (currently {state.world_tension*100:.0f}%), "
                    f"or choose a defensive casus belli (Retaliation, Defensive War, Alliance Defense)."
                )
            )
    # Monarchies/Theocracies need at least moderate tension or prestige
    elif player.ideology in {"Monarchy", "Theocracy"} and req.casus_belli not in defensive_casus:
        if state.world_tension < 0.25 and player.prestige < 25:
            raise HTTPException(
                status_code=400,
                detail="Your government lacks the prestige and public support for war at this time. Build prestige or wait for rising tensions."
            )

    war = War(
        attacker=state.player_nation_id,
        defender=target_id,
        start_turn=state.turn,
        casus_belli=req.casus_belli
    )

    # Auto-join allies
    for ally_id in player.diplomacy.defense_pacts:
        if ally_id in state.nations:
            war.attacker_allies.append(ally_id)
            state.nations[ally_id].is_at_war = True

    for ally_id in target.diplomacy.defense_pacts:
        if ally_id in state.nations and ally_id != state.player_nation_id:
            war.defender_allies.append(ally_id)
            state.nations[ally_id].is_at_war = True

    state.active_wars.append(war)
    player.is_at_war = True
    target.is_at_war = True
    state.nations[state.player_nation_id] = player
    state.nations[target_id] = target
    state.world_tension = min(1.0, state.world_tension + 0.08)

    headline = await ai_engine.generate_news_headline("war_declared", {"attacker": player.name, "defender": target.name})
    state.add_news(headline, state.player_nation_id, "war")

    await _save_state(state)
    return {"war_id": war.id, "message": f"War declared on {target.name}!"}


@app.get("/api/game/{game_id}/war/{war_id}/status")
async def get_war_status(game_id: str, war_id: str):
    state = await _get_state(game_id)
    war = next((w for w in state.active_wars if w.id == war_id), None)
    if not war:
        raise HTTPException(status_code=404, detail="War not found")
    return war.model_dump()


@app.post("/api/game/{game_id}/war/{war_id}/peace")
async def make_peace(game_id: str, war_id: str, body: dict):
    state = await _get_state(game_id)
    war = next((w for w in state.active_wars if w.id == war_id), None)
    if not war:
        raise HTTPException(status_code=404, detail="War not found")

    if war.attacker != state.player_nation_id and war.defender != state.player_nation_id:
        raise HTTPException(status_code=400, detail="Not your war")

    term_id = body.get("term_id", "status_quo")
    player = state.get_player_nation()
    winner_id = war.attacker if war.attacker_warscore >= 0 else war.defender
    loser_id = war.defender if winner_id == war.attacker else war.attacker

    winner = state.nations.get(winner_id)
    loser = state.nations.get(loser_id)

    if term_id == "annex" and winner_id == state.player_nation_id and war.attacker_warscore >= 80:
        if loser:
            # Transfer all loser's territories and occupied territories to winner
            for tid in list(loser.controlled_territories):
                if tid not in player.controlled_territories:
                    player.controlled_territories.append(tid)
            for tid in list(war.occupied_territories.keys()):
                if war.occupied_territories[tid] == winner_id and tid not in player.controlled_territories:
                    player.controlled_territories.append(tid)
            if loser_id not in player.controlled_territories:
                player.controlled_territories.append(loser_id)
            loser.controlled_territories.clear()
            loser.is_alive = False
            player.economy.gdp += loser.economy.gdp * 0.5
            player.economy.factories += max(1, loser.economy.factories // 3)
            player.prestige = min(200, player.prestige + 25)
            state.add_news(f"{player.name} annexes {loser.name}", state.player_nation_id, "war")

    elif term_id == "puppet" and winner_id == state.player_nation_id and war.attacker_warscore >= 60:
        if loser:
            loser.diplomacy.overlord = state.player_nation_id
            player.diplomacy.puppets.append(loser_id)
            player.prestige = min(200, player.prestige + 15)
            # Transfer occupied territories to winner (keep loser alive)
            for tid in list(war.occupied_territories.keys()):
                if war.occupied_territories[tid] == winner_id and tid not in player.controlled_territories:
                    player.controlled_territories.append(tid)
            state.add_news(f"{player.name} installs puppet in {loser.name}", state.player_nation_id, "war")

    elif term_id == "reparations" and winner_id == state.player_nation_id:
        if loser:
            reps = loser.economy.gdp * 0.2
            player.economy.gdp += reps
            loser.economy.gdp -= reps * 0.5
            player.prestige = min(200, player.prestige + 8)

    elif term_id == "liberate" and winner_id == state.player_nation_id and war.attacker_warscore >= 50:
        if loser:
            loser.stability = min(1.0, loser.stability + 0.15)
            loser.diplomacy.overlord = None
            if loser_id in player.diplomacy.puppets:
                player.diplomacy.puppets.remove(loser_id)
            player.prestige = min(200, player.prestige + 15)
            state.world_tension = max(0.05, state.world_tension - 0.05)
            state.add_news(f"{player.name} magnanimously liberates {loser.name}", state.player_nation_id, "diplomacy")

    # Status-quo: transfer already-occupied territories to whoever holds them
    if term_id == "status_quo":
        for territory_id, occupier_id in list(war.occupied_territories.items()):
            occupier = state.nations.get(occupier_id)
            if occupier and territory_id not in occupier.controlled_territories:
                occupier.controlled_territories.append(territory_id)
                state.nations[occupier_id] = occupier

    # End war
    state.active_wars = [w for w in state.active_wars if w.id != war_id]
    for nid in [war.attacker, war.defender] + war.attacker_allies + war.defender_allies:
        n = state.nations.get(nid)
        if n:
            n.is_at_war = False
            state.nations[nid] = n
    # Recall all player armies from this war
    for army in state.player_armies:
        if army.status == "attacking":
            army.status = "ready"
            army.assigned_target = None
            army.front_id = None

    if winner:
        state.nations[winner_id] = winner
    if loser:
        state.nations[loser_id] = loser

    state.world_tension = max(0.05, state.world_tension - 0.03)
    await _save_state(state)
    return {"message": f"Peace established. Term applied: {term_id}"}


@app.get("/api/game/{game_id}/peace_terms/{war_id}")
async def get_peace_terms(game_id: str, war_id: str):
    state = await _get_state(game_id)
    war = next((w for w in state.active_wars if w.id == war_id), None)
    if not war:
        raise HTTPException(status_code=404, detail="War not found")

    winner_id = war.attacker if war.attacker_warscore >= 0 else war.defender
    loser_id = war.defender if winner_id == war.attacker else war.attacker
    winner = state.nations.get(winner_id)
    loser = state.nations.get(loser_id)

    if not winner or not loser:
        raise HTTPException(status_code=400, detail="Nations not found")

    terms = await ai_engine.generate_peace_terms(winner.model_dump(), loser.model_dump(), war.attacker_warscore)
    # Inject liberation term for the attacker side
    if winner_id == state.player_nation_id:
        terms["available_terms"].append({
            "id": "liberate",
            "label": "Liberate Nation",
            "description": f"Grant {loser.name} full independence as a neutral state. Earns international prestige.",
            "cost_warscore": 50,
            "effects": {"prestige": 15, "world_tension_change": -0.05}
        })
    return terms


# ── Army Management ─────────────────────────────────────────────────────────


@app.get("/api/game/{game_id}/military/templates")
async def get_army_templates(game_id: str):
    return {"templates": all_templates(), "conscription_laws": all_conscription_laws()}


@app.get("/api/game/{game_id}/military/armies")
async def get_armies(game_id: str):
    state = await _get_state(game_id)
    player = state.get_player_nation()
    enriched = []
    for army in state.player_armies:
        tmpl = get_template(army.template_id)
        enriched.append({**army.model_dump(), "template": tmpl})
    fronts_data = []
    for war in state.active_wars:
        for front in war.fronts:
            def_nation = state.nations.get(front.defender_nation)
            # Count armies assigned to this front
            armies_on_front = [
                a for a in state.player_armies
                if a.front_id == front.id or (not a.front_id and a.assigned_target == front.target_territory and a.status == "attacking")
            ]
            fronts_data.append({
                **front.model_dump(),
                "defender_name": def_nation.name if def_nation else front.defender_nation,
                "army_count": len(armies_on_front),
                "warscore": war.attacker_warscore,
                "war_id": war.id,
            })
    manpower_cap = int(player.population * 0.15) if player else 0
    return {
        "armies": enriched,
        "fronts": fronts_data,
        "manpower_pool": player.military.manpower_pool if player else 0,
        "manpower_cap": manpower_cap,
        "conscription_law": player.conscription_law if player else "limited_conscription",
    }


@app.post("/api/game/{game_id}/military/army/create")
async def create_army(game_id: str, req: CreateArmyRequest):
    state = await _get_state(game_id)
    player = state.get_player_nation()
    if not player:
        raise HTTPException(status_code=404, detail="Player nation not found")

    tmpl = get_template(req.template_id)
    if not tmpl:
        raise HTTPException(status_code=400, detail=f"Unknown template: {req.template_id}")

    num_divs = max(1, min(15, req.num_divisions))
    manpower_cost = tmpl["manpower_per_div"] * num_divs
    equipment_cost = tmpl["equipment_cost"] * num_divs

    if player.military.manpower_pool < manpower_cost:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient manpower: need {manpower_cost:,}, have {player.military.manpower_pool:,}",
        )
    if player.economy.stockpile.get("equipment", 0) < equipment_cost:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient equipment: need {equipment_cost:.0f}, have {player.economy.stockpile.get('equipment', 0):.0f}",
        )
    if len(state.player_armies) >= 10:
        raise HTTPException(status_code=400, detail="Maximum 10 army groups allowed")

    name = req.name.strip() or f"{tmpl['name']} {len(state.player_armies) + 1}"
    army = ArmyDivision(
        name=name,
        nation_id=state.player_nation_id,
        template_id=req.template_id,
        num_divisions=num_divs,
        manpower=manpower_cost,
        training_turns_required=tmpl["training_turns"],
        location=state.player_nation_id,
        created_turn=state.turn,
    )

    player.military.manpower_pool -= manpower_cost
    player.economy.stockpile["equipment"] = max(
        0, player.economy.stockpile.get("equipment", 0) - equipment_cost
    )
    state.nations[state.player_nation_id] = player
    state.player_armies.append(army)

    await _save_state(state)
    await _broadcast(game_id, {"type": "state_update", "state": state.model_dump()})
    return {
        "army_id": army.id,
        "message": f"{name} enters training ({tmpl['training_turns']} turns to ready)",
    }


@app.post("/api/game/{game_id}/military/army/{army_id}/assign")
async def assign_army(game_id: str, army_id: str, req: AssignArmyRequest):
    state = await _get_state(game_id)
    army = next((a for a in state.player_armies if a.id == army_id), None)
    if not army:
        raise HTTPException(status_code=404, detail="Army not found")
    if not army.is_trained:
        raise HTTPException(status_code=400, detail="Army is still in training")

    target_id = req.target_nation_id
    if target_id not in state.nations:
        raise HTTPException(status_code=400, detail="Target nation not found")

    # Must be at war with that nation
    active_war = next(
        (w for w in state.active_wars if w.status == "ongoing" and (
            (w.attacker == state.player_nation_id and w.defender == target_id) or
            (w.defender == state.player_nation_id and w.attacker == target_id) or
            target_id in w.defender_allies or target_id in w.attacker_allies
        )),
        None,
    )
    if not active_war:
        raise HTTPException(status_code=400, detail="Not at war with that nation")

    army.assigned_target = target_id
    army.status = "attacking"

    # Determine which side we're on
    if active_war.attacker == state.player_nation_id:
        att_id, def_id = state.player_nation_id, active_war.defender
    else:
        att_id, def_id = state.player_nation_id, active_war.attacker

    sector = (req.sector or "main").strip().lower()
    valid_sectors = {"main", "north", "south", "east", "west", "flank"}
    if sector not in valid_sectors:
        sector = "main"

    # Find or create a front for this target+sector combination
    if req.open_new_front:
        # Force a new front (player wants a distinct axis of advance)
        front = WarFront(
            war_id=active_war.id,
            attacker_nation=att_id,
            defender_nation=target_id,
            target_territory=target_id,
            sector=sector,
        )
        active_war.fronts.append(front)
    else:
        existing = next(
            (f for f in active_war.fronts
             if f.target_territory == target_id and f.sector == sector and f.status == "active"),
            None,
        )
        if not existing:
            existing = WarFront(
                war_id=active_war.id,
                attacker_nation=att_id,
                defender_nation=target_id,
                target_territory=target_id,
                sector=sector,
            )
            active_war.fronts.append(existing)
        front = existing

    army.front_id = front.id

    await _save_state(state)
    await _broadcast(game_id, {"type": "state_update", "state": state.model_dump()})
    target_name = state.nations[target_id].name
    sector_label = f" [{sector.upper()}]" if sector != "main" else ""
    return {"message": f"{army.name} assigned to attack {target_name}{sector_label}"}


@app.post("/api/game/{game_id}/military/army/{army_id}/recall")
async def recall_army(game_id: str, army_id: str):
    state = await _get_state(game_id)
    army = next((a for a in state.player_armies if a.id == army_id), None)
    if not army:
        raise HTTPException(status_code=404, detail="Army not found")

    army.assigned_target = None
    army.front_id = None
    army.status = "ready" if army.is_trained else "training"

    await _save_state(state)
    await _broadcast(game_id, {"type": "state_update", "state": state.model_dump()})
    return {"message": f"{army.name} recalled"}


@app.post("/api/game/{game_id}/military/army/{army_id}/order")
async def set_army_order(game_id: str, army_id: str, body: dict):
    state = await _get_state(game_id)
    army = next((a for a in state.player_armies if a.id == army_id), None)
    if not army:
        raise HTTPException(status_code=404, detail="Army not found")

    order = body.get("order", "advance")
    if order not in ("advance", "hold"):
        raise HTTPException(status_code=400, detail="Invalid order — use: advance or hold")

    army.order = order
    await _save_state(state)
    await _broadcast(game_id, {"type": "state_update", "state": state.model_dump()})
    return {"message": f"{army.name}: order set to {order}"}


@app.delete("/api/game/{game_id}/military/army/{army_id}")
async def disband_army(game_id: str, army_id: str):
    state = await _get_state(game_id)
    player = state.get_player_nation()
    army = next((a for a in state.player_armies if a.id == army_id), None)
    if not army:
        raise HTTPException(status_code=404, detail="Army not found")

    # Return some manpower on disband
    if army.is_trained and player:
        returned = int(army.manpower * 0.5 * army.strength)
        cap = int(player.population * 0.15)
        player.military.manpower_pool = min(cap, player.military.manpower_pool + returned)
        state.nations[state.player_nation_id] = player

    state.player_armies = [a for a in state.player_armies if a.id != army_id]
    await _save_state(state)
    await _broadcast(game_id, {"type": "state_update", "state": state.model_dump()})
    return {"message": f"{army.name} disbanded"}


@app.post("/api/game/{game_id}/military/conscription")
async def set_conscription(game_id: str, req: ConscriptionRequest):
    state = await _get_state(game_id)
    player = state.get_player_nation()
    if not player:
        raise HTTPException(status_code=400, detail="No player nation")

    law = get_conscription_law(req.law_id)
    if not law:
        raise HTTPException(status_code=400, detail=f"Unknown conscription law: {req.law_id}")

    pp_cost = law["political_power_cost"]
    if player.political_power < pp_cost:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient political power: need {pp_cost}, have {player.political_power:.0f}",
        )

    player.political_power -= pp_cost
    player.conscription_law = req.law_id
    # Apply stability bonus/penalty
    player.stability = max(0.05, min(1.0, player.stability + law["stability_bonus"]))
    state.nations[state.player_nation_id] = player

    await _save_state(state)
    await _broadcast(game_id, {"type": "state_update", "state": state.model_dump()})
    return {"message": f"Conscription law changed to {law['name']}"}


@app.get("/api/game/{game_id}/military/war-fronts")
async def get_war_fronts(game_id: str):
    state = await _get_state(game_id)
    result = []
    for war in state.active_wars:
        for front in war.fronts:
            att = state.nations.get(front.attacker_nation)
            def_ = state.nations.get(front.defender_nation)
            result.append({
                **front.model_dump(),
                "attacker_name": att.name if att else front.attacker_nation,
                "defender_name": def_.name if def_ else front.defender_nation,
                "warscore": war.attacker_warscore,
            })
    return {"fronts": result}


# ── Economy ─────────────────────────────────────────────────────────────────


@app.get("/api/game/{game_id}/economy/policy")
async def get_economy_policy(game_id: str):
    state = await _get_state(game_id)
    player = state.get_player_nation()
    if not player:
        raise HTTPException(status_code=400, detail="No player nation")
    return player.economy.model_dump()


@app.post("/api/game/{game_id}/economy/policy")
async def set_economy_policy(game_id: str, policy: dict):
    state = await _get_state(game_id)
    player = state.get_player_nation()
    if not player:
        raise HTTPException(status_code=400, detail="No player nation")

    eco = player.economy
    if "tax_rate" in policy:
        eco.tax_rate = max(0.05, min(0.70, float(policy["tax_rate"])))
    if "gov_spending" in policy:
        eco.gov_spending = max(0.05, min(0.80, float(policy["gov_spending"])))
    if "trade_openness" in policy:
        eco.trade_openness = max(0.0, min(1.0, float(policy["trade_openness"])))
    if "nationalization" in policy:
        eco.nationalization = max(0.0, min(1.0, float(policy["nationalization"])))
    if "military_spending" in policy:
        player.military.military_spending = max(0.01, min(0.30, float(policy["military_spending"])))
    if "research_focus" in policy:
        focus = str(policy["research_focus"])
        if focus in ("industry", "military", "diplomacy"):
            player.research_focus = focus

    player.economy = eco
    state.nations[state.player_nation_id] = player
    await _save_state(state)
    return {"message": "Economic policy updated", "economy": eco.model_dump()}


# ── Advanced Diplomacy ──────────────────────────────────────────────────────

@app.post("/api/game/{game_id}/diplomacy/resource-trade")
async def propose_resource_trade(game_id: str, req: ResourceTradeRequest):
    """Propose a per-turn resource exchange with another nation."""
    state = await _get_state(game_id)
    player = state.get_player_nation()
    if not player:
        raise HTTPException(status_code=400, detail="No player nation")

    target_id = game_logic.find_nation_id(state, req.target_nation)
    if not target_id:
        raise HTTPException(status_code=404, detail="Target nation not found")
    target = state.nations[target_id]

    response = await ai_engine.generate_resource_trade_response(
        target.model_dump(), player.model_dump(),
        req.offer_resource, req.offer_amount,
        req.request_resource, req.request_amount
    )

    if response.get("accepted"):
        trade = ResourceTradeOffer(
            initiator_id=state.player_nation_id,
            target_id=target_id,
            offer_resource=req.offer_resource,
            offer_amount=req.offer_amount,
            request_resource=req.request_resource,
            request_amount=req.request_amount,
        )
        state.resource_trades.append(trade)
        player.diplomacy.relations[target_id] = min(100, player.diplomacy.relations.get(target_id, 0) + 3)
        target.diplomacy.relations[state.player_nation_id] = min(100, target.diplomacy.relations.get(state.player_nation_id, 0) + 3)
        state.nations[state.player_nation_id] = player
        state.nations[target_id] = target
        state.add_news(
            f"{player.name} and {target.name} sign resource trade agreement",
            state.player_nation_id, "diplomacy"
        )
        await _save_state(state)

    return {
        "accepted": response.get("accepted"),
        "response_message": response.get("response_message", ""),
        "counteroffer": response.get("counteroffer"),
    }


@app.get("/api/game/{game_id}/resource-trades")
async def get_resource_trades(game_id: str):
    state = await _get_state(game_id)
    player_trades = [t.model_dump() for t in state.resource_trades
                     if t.initiator_id == state.player_nation_id or t.target_id == state.player_nation_id]
    return {"trades": player_trades}


@app.delete("/api/game/{game_id}/resource-trades/{trade_id}")
async def cancel_resource_trade(game_id: str, trade_id: str):
    state = await _get_state(game_id)
    trade = next((t for t in state.resource_trades if t.id == trade_id), None)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    if trade.initiator_id != state.player_nation_id:
        raise HTTPException(status_code=403, detail="Not your trade")
    state.resource_trades = [t for t in state.resource_trades if t.id != trade_id]
    await _save_state(state)
    return {"message": "Trade cancelled"}


@app.post("/api/game/{game_id}/diplomacy/request-troops")
async def request_troops(game_id: str, req: TroopRequest):
    """Ask an ally to send troops to an active war."""
    state = await _get_state(game_id)
    player = state.get_player_nation()
    if not player:
        raise HTTPException(status_code=400, detail="No player nation")
    if not player.is_at_war:
        raise HTTPException(status_code=400, detail="Not at war")

    target_id = game_logic.find_nation_id(state, req.target_nation)
    if not target_id:
        raise HTTPException(status_code=404, detail="Nation not found")
    target = state.nations[target_id]

    war = next((w for w in state.active_wars if w.id == req.war_id), None)
    if not war:
        raise HTTPException(status_code=404, detail="War not found")

    response = await ai_engine.generate_troop_request_response(
        target.model_dump(), player.model_dump(), req.war_id, req.troops_requested
    )

    if response.get("accepted"):
        troops = int(response.get("troops_sent", 0))
        if troops > 0:
            # Move troops from target to the war (reduce target's army, boost our side)
            target.military.army_size = max(0, target.military.army_size - troops)
            war.contributed_troops[target_id] = war.contributed_troops.get(target_id, 0) + troops
            # Add them as an attacker ally if not already
            if target_id not in war.attacker_allies:
                war.attacker_allies.append(target_id)
                target.is_at_war = True
            state.nations[target_id] = target
            state.add_news(
                f"{target.name} sends {troops:,} troops to aid {player.name}",
                state.player_nation_id, "war"
            )
            await _save_state(state)

    return {
        "accepted": response.get("accepted"),
        "troops_sent": response.get("troops_sent", 0),
        "response_message": response.get("response_message", ""),
    }


@app.post("/api/game/{game_id}/diplomacy/buy-technology")
async def buy_technology(game_id: str, req: TechPurchaseRequest):
    """Purchase a tech level advance from a more advanced nation."""
    state = await _get_state(game_id)
    player = state.get_player_nation()
    if not player:
        raise HTTPException(status_code=400, detail="No player nation")

    target_id = game_logic.find_nation_id(state, req.target_nation)
    if not target_id:
        raise HTTPException(status_code=404, detail="Nation not found")
    target = state.nations[target_id]

    # Seller must be ahead in that tech branch
    seller_level = target.tech_levels.get(req.tech_branch, 1)
    buyer_level = player.tech_levels.get(req.tech_branch, 1)
    if seller_level <= buyer_level:
        raise HTTPException(status_code=400, detail=f"{target.name} is not ahead in {req.tech_branch} technology")
    if player.economy.gdp < req.price_gdp:
        raise HTTPException(status_code=400, detail="Insufficient GDP for this purchase")

    response = await ai_engine.generate_tech_purchase_response(
        target.model_dump(), player.model_dump(), req.tech_branch, req.price_gdp
    )

    if response.get("accepted"):
        # Transfer GDP, advance buyer's tech by 1
        player.economy.gdp -= req.price_gdp
        target.economy.gdp += req.price_gdp * 0.8
        player.tech_levels[req.tech_branch] = min(10, buyer_level + 1)
        player.diplomacy.relations[target_id] = min(100, player.diplomacy.relations.get(target_id, 0) + 5)
        target.diplomacy.relations[state.player_nation_id] = min(100, target.diplomacy.relations.get(state.player_nation_id, 0) + 5)
        state.nations[state.player_nation_id] = player
        state.nations[target_id] = target
        state.add_news(
            f"{player.name} acquires {req.tech_branch} technology from {target.name}",
            state.player_nation_id, "diplomacy"
        )
        await _save_state(state)

    return {
        "accepted": response.get("accepted"),
        "response_message": response.get("response_message", ""),
        "new_tech_level": player.tech_levels.get(req.tech_branch, 1) if response.get("accepted") else buyer_level,
    }


@app.post("/api/game/{game_id}/diplomacy/joint-research")
async def propose_joint_research(game_id: str, req: JointResearchRequest):
    """Propose joint research with another nation — both sides get double research speed."""
    state = await _get_state(game_id)
    player = state.get_player_nation()
    if not player:
        raise HTTPException(status_code=400, detail="No player nation")

    target_id = game_logic.find_nation_id(state, req.target_nation)
    if not target_id:
        raise HTTPException(status_code=404, detail="Nation not found")
    target = state.nations[target_id]

    response = await ai_engine.generate_joint_research_response(
        target.model_dump(), player.model_dump(), req.tech_branch
    )

    if response.get("accepted"):
        # Both nations get a research point bonus (simulated as a one-time grant)
        bonus_rp = 25.0
        player.research_points += bonus_rp
        target.research_points += bonus_rp
        # Both set research focus to the agreed branch
        player.research_focus = req.tech_branch
        target.research_focus = req.tech_branch
        player.diplomacy.relations[target_id] = min(100, player.diplomacy.relations.get(target_id, 0) + 4)
        target.diplomacy.relations[state.player_nation_id] = min(100, target.diplomacy.relations.get(state.player_nation_id, 0) + 4)
        state.nations[state.player_nation_id] = player
        state.nations[target_id] = target
        state.add_news(
            f"{player.name} and {target.name} launch joint {req.tech_branch} research",
            state.player_nation_id, "diplomacy"
        )
        await _save_state(state)

    return {
        "accepted": response.get("accepted"),
        "response_message": response.get("response_message", ""),
    }


@app.post("/api/game/{game_id}/diplomacy/upgrade-alliance")
async def upgrade_alliance(game_id: str, req: AllianceUpgradeRequest):
    """Upgrade the alliance tier with another nation (1=non-aggression, 2=defense pact, 3=full)."""
    state = await _get_state(game_id)
    player = state.get_player_nation()
    if not player:
        raise HTTPException(status_code=400, detail="No player nation")
    if req.target_tier not in (1, 2, 3):
        raise HTTPException(status_code=400, detail="target_tier must be 1, 2, or 3")

    target_id = game_logic.find_nation_id(state, req.target_nation)
    if not target_id:
        raise HTTPException(status_code=404, detail="Nation not found")
    target = state.nations[target_id]

    current_tier = player.diplomacy.alliance_tier.get(target_id, 0)
    if req.target_tier <= current_tier:
        raise HTTPException(status_code=400, detail="Already at that tier or higher")

    # Must go one tier at a time
    if req.target_tier > current_tier + 1:
        raise HTTPException(status_code=400, detail=f"Must upgrade one tier at a time (currently tier {current_tier})")

    response = await ai_engine.generate_diplomatic_response(
        target.model_dump(), player.model_dump(),
        f"alliance_tier_{req.target_tier}", {}
    )

    if response.get("accepted"):
        # Update tier on both sides
        player.diplomacy.alliance_tier[target_id] = req.target_tier
        target.diplomacy.alliance_tier[state.player_nation_id] = req.target_tier

        tier_names = {1: "Non-Aggression Pact", 2: "Defense Pact", 3: "Full Military Alliance"}
        tier_name = tier_names[req.target_tier]

        # Sync with legacy lists so existing war-joining logic keeps working
        if req.target_tier >= 2 and target_id not in player.diplomacy.defense_pacts:
            player.diplomacy.defense_pacts.append(target_id)
            target.diplomacy.defense_pacts.append(state.player_nation_id)
        if req.target_tier >= 3 and target_id not in player.diplomacy.alliances:
            player.diplomacy.alliances.append(target_id)
            target.diplomacy.alliances.append(state.player_nation_id)

        rel_bonus = req.target_tier * 8
        player.diplomacy.relations[target_id] = min(100, player.diplomacy.relations.get(target_id, 0) + rel_bonus)
        target.diplomacy.relations[state.player_nation_id] = min(100, target.diplomacy.relations.get(state.player_nation_id, 0) + rel_bonus)
        state.nations[state.player_nation_id] = player
        state.nations[target_id] = target
        state.add_news(
            f"{player.name} and {target.name} sign {tier_name}",
            state.player_nation_id, "diplomacy"
        )
        await _save_state(state)

    return {
        "accepted": response.get("accepted"),
        "response_message": response.get("response_message", ""),
        "counteroffer": response.get("counteroffer"),
        "new_tier": req.target_tier if response.get("accepted") else current_tier,
    }


@app.get("/api/game/{game_id}/nation/{nation_id}")
async def get_nation_detail(game_id: str, nation_id: str):
    state = await _get_state(game_id)
    nation = state.nations.get(nation_id)
    if not nation:
        raise HTTPException(status_code=404, detail="Nation not found")
    return nation.model_dump()


@app.get("/api/game/{game_id}/tech-tree")
async def get_tech_tree(game_id: str):
    """Return all tech nodes with their researched status for this game."""
    from backend.tech_nodes import get_all_nodes, can_research
    state = await _get_state(game_id)
    player = state.get_player_nation()
    if not player:
        raise HTTPException(status_code=400, detail="No player nation")

    researched = set(player.tech_levels.get("researched_nodes", []))
    in_progress = {p.node_id: p for p in player.research_projects}
    nodes = []
    for node in get_all_nodes(state.year):
        researchable, reason = can_research(node["id"], researched, state.year)
        nodes.append({**node, "researched": node["id"] in researched,
                      "can_research": researchable, "blocked_reason": reason,
                      "in_progress": node["id"] in in_progress})
    return {
        "nodes": nodes,
        "research_points": player.research_points,
        "slots_unlocked": player.research_slots_unlocked,
        "slots_max": player.research_slots_max,
        "projects": [p.model_dump() for p in player.research_projects],
        "seconds_per_month": SECONDS_PER_MONTH,
    }


@app.post("/api/game/{game_id}/research/start")
async def start_research(game_id: str, body: dict):
    from backend.tech_nodes import get_node, can_research
    from backend.models import ResearchProject
    state = await _get_state(game_id)
    player = state.get_player_nation()
    if not player:
        raise HTTPException(status_code=400, detail="No player nation")

    node_id = body.get("node_id", "")
    slot = int(body.get("slot", -1))
    if slot < 0 or slot >= player.research_slots_unlocked:
        raise HTTPException(status_code=400, detail="Invalid research slot")

    if any(p.slot == slot for p in player.research_projects):
        raise HTTPException(status_code=400, detail="Slot already in use")

    node = get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Tech node not found")

    researched = set(player.tech_levels.get("researched_nodes", []))
    ok, reason = can_research(node_id, researched, state.year)
    if not ok:
        raise HTTPException(status_code=400, detail=reason)

    player.research_projects.append(ResearchProject(
        slot=slot,
        node_id=node_id,
        progress_days=0.0,
        total_days=node.get("days", 60),
    ))
    state.nations[state.player_nation_id] = player
    await _save_state(state)

    return {"message": "Research started", "projects": [p.model_dump() for p in player.research_projects]}


@app.post("/api/game/{game_id}/research/cancel")
async def cancel_research(game_id: str, body: dict):
    state = await _get_state(game_id)
    player = state.get_player_nation()
    if not player:
        raise HTTPException(status_code=400, detail="No player nation")

    slot = int(body.get("slot", -1))
    before = len(player.research_projects)
    player.research_projects = [p for p in player.research_projects if p.slot != slot]
    if len(player.research_projects) == before:
        raise HTTPException(status_code=404, detail="No research in that slot")

    state.nations[state.player_nation_id] = player
    await _save_state(state)
    return {"message": "Research cancelled", "projects": [p.model_dump() for p in player.research_projects]}


@app.post("/api/game/{game_id}/tech-tree/research")
async def research_node(game_id: str, body: dict):
    """Spend research points to unlock a tech node."""
    from backend.tech_nodes import get_node, can_research
    state = await _get_state(game_id)
    player = state.get_player_nation()
    if not player:
        raise HTTPException(status_code=400, detail="No player nation")

    node_id = body.get("node_id", "")
    node = get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Tech node not found")

    researched = set(player.tech_levels.get("researched_nodes", []))
    ok, reason = can_research(node_id, researched)
    if not ok:
        raise HTTPException(status_code=400, detail=reason)

    cost = node["cost"]
    if player.research_points < cost:
        raise HTTPException(status_code=400, detail=f"Need {cost} research points (have {player.research_points:.0f})")

    # Deduct cost and mark researched
    player.research_points -= cost
    researched.add(node_id)
    player.tech_levels["researched_nodes"] = list(researched)

    # Apply unlocks
    effects = node.get("unlocks", {})
    from backend.game_logic import apply_issue_effects
    eco = player.economy
    mil = player.military

    for key, val in effects.items():
        if key == "gdp_growth": eco.gdp_growth = min(0.15, eco.gdp_growth + val)
        elif key == "inflation": eco.inflation = max(0.0, eco.inflation + val)
        elif key == "unemployment": eco.unemployment = max(0.01, eco.unemployment + val)
        elif key == "trade_openness": eco.trade_openness = min(1.0, eco.trade_openness + val)
        elif key == "factories": eco.factories += int(val)
        elif key == "arms_factories": eco.arms_factories += int(val)
        elif key == "research_labs": eco.research_labs += int(val)
        elif key == "morale": mil.morale = min(1.0, mil.morale + val)
        elif key == "equipment_level": mil.equipment_level = min(1.0, mil.equipment_level + val)
        elif key == "army_size": mil.army_size += int(val)
        elif key == "stability": player.stability = min(1.0, player.stability + val)
        elif key == "war_support": player.war_support = min(1.0, player.war_support + val)
        elif key == "prestige": player.prestige = min(200, player.prestige + val)
        elif key == "happiness": player.happiness = min(1.0, player.happiness + val)
        elif key == "research_points": player.research_points += val

    player.economy = eco
    player.military = mil
    state.nations[state.player_nation_id] = player
    state.add_news(f"{player.name} develops {node['name']}", state.player_nation_id, "politics")
    await _save_state(state)

    return {
        "success": True,
        "node_name": node["name"],
        "research_points_remaining": player.research_points,
        "unlock_text": node.get("unlock_text", ""),
    }


@app.get("/api/game/{game_id}/policies")
async def get_policies(game_id: str):
    from backend.policies_library import get_policies_status, MAX_ACTIVE_POLICIES
    state = await _get_state(game_id)
    player = state.get_player_nation()
    if not player:
        raise HTTPException(status_code=400, detail="No player nation")
    return {
        "policies": get_policies_status(
            player.ideology,
            player.active_policies,
            player.is_at_war,
            player.political_power,
        ),
        "active_count": len(player.active_policies),
        "max_active": MAX_ACTIVE_POLICIES,
        "political_power": player.political_power,
    }


@app.post("/api/game/{game_id}/toggle-policy")
async def toggle_policy(game_id: str, body: dict):
    from backend.policies_library import get_policy, MAX_ACTIVE_POLICIES, get_policy_cost
    policy_id = body.get("policy_id", "")
    state = await _get_state(game_id)
    player = state.get_player_nation()
    if not player:
        raise HTTPException(status_code=400, detail="No player nation")

    policy = get_policy(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    if policy.get("requires_at_war") and not player.is_at_war:
        raise HTTPException(status_code=400, detail="This policy requires being at war")

    cost = get_policy_cost(policy)
    if policy_id in player.active_policies:
        player.active_policies.remove(policy_id)
        action = "deactivated"
    else:
        if player.political_power < cost:
            raise HTTPException(status_code=400, detail=f"Need {cost} political power to activate")
        if len(player.active_policies) >= MAX_ACTIVE_POLICIES:
            raise HTTPException(
                status_code=400,
                detail=f"Maximum {MAX_ACTIVE_POLICIES} active policies. Deactivate one first."
            )
        conflicts = [c for c in policy.get("conflicts", []) if c in player.active_policies]
        if conflicts:
            from backend.policies_library import get_policy as gp
            names = [gp(c)["name"] for c in conflicts if gp(c)]
            raise HTTPException(status_code=400, detail=f"Conflicts with: {', '.join(names)}")
        player.active_policies.append(policy_id)
        player.political_power = max(0.0, player.political_power - cost)
        action = "activated"

    state.nations[state.player_nation_id] = player
    await _save_state(state)
    from backend.policies_library import get_policies_status, MAX_ACTIVE_POLICIES as MAX_POL
    return {
        "action": action,
        "policy_name": policy["name"],
        "policies": get_policies_status(
            player.ideology,
            player.active_policies,
            player.is_at_war,
            player.political_power,
        ),
        "active_count": len(player.active_policies),
        "max_active": MAX_POL,
        "political_power": player.political_power,
    }


@app.get("/api/game/{game_id}/stream/news")
async def stream_news(game_id: str):
    state = await _get_state(game_id)
    player = state.get_player_nation()
    if not player:
        raise HTTPException(status_code=400, detail="No player nation")

    if ai_engine.AI_ENABLED is False:
        async def generate_static():
            headlines = [
                "Industrial output surges across key regions",
                "Border tensions ease after backchannel talks",
                "New trade routes open between allied nations",
            ]
            for h in headlines:
                yield f"data: {json.dumps({'chunk': h})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(generate_static(), media_type="text/event-stream")

    context = {
        "nation": player.name,
        "turn": state.turn,
        "year": state.year,
        "world_tension": state.world_tension
    }

    async def generate():
        async for chunk in ai_engine.stream_ai([
            {"role": "system", "content": "Generate 3 short news headlines for a grand strategy game world. One per line."},
            {"role": "user", "content": f"Nation: {player.name} ({player.ideology}), Year: {state.year}, World tension: {state.world_tension:.0%}. Generate 3 current news headlines."}
        ], temperature=0.9, max_tokens=200):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ── Sandbox / Cheat Panel ───────────────────────────────────────────────────


@app.post("/api/game/{game_id}/sandbox")
async def sandbox_action(game_id: str, body: dict):
    """Developer sandbox: instant cheats for testing game features."""
    state = await _get_state(game_id)
    player = state.get_player_nation()
    if not player:
        raise HTTPException(status_code=400, detail="No player nation")

    action = body.get("action", "")
    messages = []

    if action == "add_manpower":
        amount = int(body.get("amount", 1_000_000))
        player.military.manpower_pool = min(
            int(player.population * 0.25),
            player.military.manpower_pool + amount,
        )
        messages.append(f"+{amount:,} manpower")

    elif action == "add_equipment":
        amount = float(body.get("amount", 5000))
        player.economy.stockpile["equipment"] = min(
            9999, player.economy.stockpile.get("equipment", 0) + amount
        )
        messages.append(f"+{amount:.0f} equipment")

    elif action == "add_political_power":
        amount = float(body.get("amount", 300))
        player.political_power = min(999, player.political_power + amount)
        messages.append(f"+{amount:.0f} political power")

    elif action == "add_stability":
        player.stability = min(1.0, player.stability + 0.25)
        player.war_support = min(1.0, player.war_support + 0.25)
        messages.append("Stability and war support boosted")

    elif action == "boost_economy":
        player.economy.gdp = player.economy.gdp * 1.5
        for res in ["steel", "fuel", "equipment"]:
            player.economy.stockpile[res] = min(9999, player.economy.stockpile.get(res, 0) + 2000)
        player.economy.gdp_growth = 0.08
        messages.append("Economy boosted: GDP ×1.5, stockpiles +2000 each")

    elif action == "instant_train":
        count = 0
        for army in state.player_armies:
            if not army.is_trained:
                army.training_progress = army.training_turns_required
                army.is_trained = True
                army.status = "ready"
                army.organization = 1.0
                count += 1
        messages.append(f"{count} armies instantly trained")

    elif action == "max_warscore":
        for war in state.active_wars:
            if war.attacker == state.player_nation_id or state.player_nation_id in war.attacker_allies:
                war.attacker_warscore = 100
            elif war.defender == state.player_nation_id or state.player_nation_id in war.defender_allies:
                war.attacker_warscore = -100
        messages.append("Warscore set to maximum")

    elif action == "capture_all_fronts":
        from backend.models import WarFront
        for war in state.active_wars:
            for front in war.fronts:
                if front.attacker_nation == state.player_nation_id:
                    front.progress = 1.0
                    front.status = "captured"
                    war.occupied_territories[front.target_territory] = state.player_nation_id
                    war.attacker_warscore = min(100, war.attacker_warscore + 20)
        messages.append("All fronts captured")

    elif action == "add_armies":
        from backend.models import ArmyDivision
        templates = ["infantry", "armor", "motorized"]
        for i, tmpl_id in enumerate(templates):
            army = ArmyDivision(
                name=f"Test {tmpl_id.title()} {i+1}",
                nation_id=state.player_nation_id,
                template_id=tmpl_id,
                num_divisions=3,
                manpower=30000,
                training_turns_required=0,
                is_trained=True,
                organization=1.0,
                status="ready",
                location=state.player_nation_id,
                created_turn=state.turn,
            )
            state.player_armies.append(army)
        messages.append("Added 3 test army groups (infantry/armor/motorized)")

    elif action == "reduce_tension":
        state.world_tension = max(0.05, state.world_tension - 0.3)
        messages.append(f"World tension → {state.world_tension*100:.0f}%")

    elif action == "increase_tension":
        state.world_tension = min(1.0, state.world_tension + 0.3)
        messages.append(f"World tension → {state.world_tension*100:.0f}%")

    else:
        raise HTTPException(status_code=400, detail=f"Unknown sandbox action: {action}")

    state.nations[state.player_nation_id] = player
    await _save_state(state)
    await _broadcast(game_id, {"type": "state_update", "state": state.model_dump()})
    return {"messages": messages, "action": action}


# ── Espionage ──────────────────────────────────────────────────────────────

_SPY_MISSIONS: dict[str, dict] = {
    "steal_blueprints": {"cost": 40, "effect": "research", "value": 25},
    "sabotage_industry": {"cost": 60, "effect": "industry", "value": -0.15},
    "assassinate_leader": {"cost": 80, "effect": "stability", "value": -0.20},
    "propaganda_campaign": {"cost": 30, "effect": "war_support", "value": -0.10},
    "counter_intel": {"cost": 20, "effect": "defense", "value": 0.25},
}


@app.post("/api/game/{game_id}/espionage/launch")
async def launch_spy_mission(game_id: str, body: dict):
    state = await _get_state(game_id)
    player = state.get_player_nation()
    if not player:
        raise HTTPException(status_code=400, detail="No player nation")

    mission_id = body.get("mission_id", "")
    target_name = body.get("target_nation", "")
    mission = _SPY_MISSIONS.get(mission_id)
    if not mission:
        raise HTTPException(status_code=400, detail=f"Unknown mission: {mission_id}")

    cost = mission["cost"]
    if player.espionage_points < cost:
        raise HTTPException(status_code=400, detail=f"Not enough intel points ({player.espionage_points:.0f}/{cost})")

    # Find target nation
    target = next((n for n in state.nations.values() if n.name.lower() == target_name.lower()), None)

    player.espionage_points -= cost
    effect = mission["effect"]
    value = mission["value"]
    msg = ""

    if effect == "research":
        player.research_points = min(100, player.research_points + value)
        msg = f"Blueprints stolen — +{value} Research Points"
    elif effect == "industry" and target:
        target.economy.gdp_growth = max(-0.15, target.economy.gdp_growth + value)
        msg = f"Sabotage successful — {target.name} industry disrupted"
    elif effect == "stability" and target:
        target.stability = max(0.0, target.stability + value)
        msg = f"Assassination attempt — {target.name} stability reduced"
    elif effect == "war_support" and target:
        target.war_support = max(0.0, target.war_support + value)
        msg = f"Propaganda spread — {target.name} war support reduced"
    elif effect == "defense":
        msg = "Counter-intelligence hardened — your agencies are more secure"
    else:
        msg = f"Operation completed" + (f" against {target_name}" if target_name else "")

    state.nations[state.player_nation_id] = player
    if target:
        state.nations[target.id] = target
    await _save_state(state)
    return {"message": msg, "espionage_points": player.espionage_points}


# ── WebSocket ──────────────────────────────────────────────────────────────

@app.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    await websocket.accept()
    if game_id not in _ws_connections:
        _ws_connections[game_id] = []
    _ws_connections[game_id].append(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Handle client ping
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        if game_id in _ws_connections and websocket in _ws_connections[game_id]:
            _ws_connections[game_id].remove(websocket)


# ── Static Files ────────────────────────────────────────────────────────────

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
async def root():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/{path:path}")
async def catch_all(path: str):
    file_path = os.path.join(FRONTEND_DIR, path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
