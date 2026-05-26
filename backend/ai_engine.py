import httpx
import json
import asyncio
import re
import random
import os
from typing import AsyncGenerator

AI_BASE_URL = "http://10.0.0.80:1234/v1"
AI_ENABLED = os.getenv("AI_ENABLED", "0") == "1"
MODEL_ID = None
# Qwen3 always generates ~30-50 thinking tokens before content (~6-8s overhead).
# Simple calls take ~10-15s, complex ones ~20-30s. 60s covers most cases.
REQUEST_TIMEOUT = httpx.Timeout(connect=8.0, read=60.0, write=10.0, pool=5.0)


async def get_model_id() -> str:
    global MODEL_ID
    if MODEL_ID:
        return MODEL_ID
    if not AI_ENABLED:
        MODEL_ID = "disabled"
        return MODEL_ID
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{AI_BASE_URL}/models")
            data = r.json()
            models = data.get("data", [])
            if models:
                MODEL_ID = models[0]["id"]
                return MODEL_ID
    except Exception:
        pass
    MODEL_ID = "qwen3-9b"
    return MODEL_ID


def _extract_json(text: str) -> dict | list | None:
    text = text.strip()
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'```\s*$', '', text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    # Find which comes first: array or object, and use greedy match from there
    obj_pos = text.find('{')
    arr_pos = text.find('[')
    if arr_pos >= 0 and (obj_pos < 0 or arr_pos < obj_pos):
        # Array comes first — try greedy array match
        match = re.search(r'\[[\s\S]*\]', text)
    elif obj_pos >= 0:
        # Object comes first — try greedy object match
        match = re.search(r'\{[\s\S]*\}', text)
    else:
        match = None
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    return None


async def _call_ai(messages: list[dict], temperature: float = 0.7, max_tokens: int = 800, prefill: str = "") -> str:
    """
    Streams the AI response, skipping reasoning_content tokens (Qwen3 thinking).
    Collects actual content tokens and returns as soon as we have a complete response.
    Falls back to full non-streaming after 5s if streaming fails.
    """
    model = await get_model_id()
    if not AI_ENABLED:
        raise RuntimeError("AI disabled")
    all_messages = list(messages)
    if prefill:
        all_messages.append({"role": "assistant", "content": prefill})

    payload = {
        "model": model,
        "messages": all_messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
        "lmstudio_extended_chat_options": {"enable_thinking": False},
        "enable_thinking": False,
    }

    content_buf = prefill  # start with prefill so JSON is complete
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            async with client.stream("POST", f"{AI_BASE_URL}/chat/completions", json=payload) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    raw_chunk = line[6:]
                    if raw_chunk == "[DONE]":
                        break
                    try:
                        chunk_data = json.loads(raw_chunk)
                        delta = chunk_data["choices"][0]["delta"]
                        # Only collect actual content, skip reasoning_content (thinking tokens)
                        piece = delta.get("content", "")
                        if piece:
                            content_buf += piece
                    except Exception:
                        continue
        return content_buf.strip()
    except Exception as e:
        raise


async def stream_ai(messages: list[dict], temperature: float = 0.7, max_tokens: int = 200) -> AsyncGenerator[str, None]:
    model = await get_model_id()
    if not AI_ENABLED:
        yield "[AI disabled]"
        return
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
        "lmstudio_extended_chat_options": {"enable_thinking": False},
        "enable_thinking": False,
    }
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            async with client.stream("POST", f"{AI_BASE_URL}/chat/completions", json=payload) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        chunk = line[6:]
                        if chunk == "[DONE]":
                            break
                        try:
                            data = json.loads(chunk)
                            delta = data["choices"][0]["delta"].get("content", "")
                            if delta:
                                yield delta
                        except Exception:
                            continue
    except Exception as e:
        yield f"[{str(e)[:60]}]"


# ── World Generation ─────────────────────────────────────────────────────────

# Prevent concurrent world-gen requests from stacking (e.g. user clicks Start twice)
_world_gen_lock = asyncio.Lock()

async def generate_world_state(era_id: str, era_name: str, player_nation: str, ideology: str, major_nations: list[str]) -> dict:
    """Generate starting world via streaming so we don't block for 180s on slow models."""
    if not AI_ENABLED:
        return {}
    # Only one world gen at a time — callers that arrive while one is running wait for it
    async with _world_gen_lock:
        nations_list = ", ".join(major_nations[:7])
        # Compact schema — fewer fields means fewer tokens (~1200 total vs 3000 before)
        msg = (
            f"/no_think Era:{era_name}. Player:{player_nation}({ideology}). "
            f"Nations:{nations_list}. "
            f'Return ONLY JSON, no extra text: {{"nations":{{"NationName":{{'
            f'"capital":"","leader":"","ideology":"Liberal Democracy",'
            f'"government_type":"Republic","population":10000000,'
            f'"stability":0.7,"war_support":0.5,"prestige":50,'
            f'"economy":{{"gdp":100,"gdp_growth":0.03,"unemployment":0.08,"inflation":0.02}},'
            f'"military":{{"army_size":100000,"equipment_level":0.7,"morale":0.8,"military_spending":0.05}},'
            f'"diplomacy":{{"alliances":[],"defense_pacts":[],"trade_deals":[],"sanctions_against":[],"relations":{{}}}},'
            f'"personality":{{"aggression":0.5,"economic_priority":"balanced","diplomatic_tendency":"neutral",'
            f'"historical_grievances":[],"core_claims":[]}}}}}},"world_tension":0.3}}'
        )
        try:
            # Use streaming + prefill so the model skips thinking and generates JSON directly.
            # The 60s per-chunk read timeout in _call_ai is sufficient.
            raw = await _call_ai(
                [{"role": "user", "content": msg}],
                temperature=0.5,
                max_tokens=1800,
                prefill='{"nations":{"',
            )
            result = _extract_json(raw)
            if result and "nations" in result:
                print(f"AI world gen OK: {len(result['nations'])} nations")
                return result
            print(f"AI world gen JSON invalid, using fallback. Got: {repr(raw[:120])}")
        except Exception as e:
            print(f"AI world gen error ({type(e).__name__}): {e}")
        return {}


# ── Nation Decisions ─────────────────────────────────────────────────────────

async def generate_nation_decision(game_state_summary: dict, nation_id: str) -> dict:
    nation = game_state_summary["nations"].get(nation_id, {})
    top_rel = dict(list(nation.get("diplomacy", {}).get("relations", {}).items())[:3])

    msg = (
        f"/no_think {nation.get('name')}({nation.get('ideology')}) "
        f"GDP:{nation.get('economy',{}).get('gdp',0):.0f} "
        f"Army:{nation.get('military',{}).get('army_size',0)} "
        f"Aggression:{nation.get('personality',{}).get('aggression',0.5):.1f} "
        f"Relations:{json.dumps(top_rel)} "
        f'Pick 1 action, return ONLY JSON: {{"action":"improve_relations","target":"NationName or null","reason":"brief"}}'
    )
    try:
        raw = await _call_ai([{"role": "user", "content": msg}], temperature=0.7, max_tokens=600, prefill='{"action":')
        result = _extract_json(raw)
        if result and "action" in result:
            return {"actions": [result]}
    except Exception as e:
        print(f"AI nation decision skipped ({type(e).__name__})")
    return {"actions": []}


# ── Issue Generation ─────────────────────────────────────────────────────────

# Pre-built fallback issue pool — used when AI is too slow
_FALLBACK_ISSUES = [
    {
        "title": "Labor Strike Threatens Industry",
        "description": "Factory workers across major industrial centers have walked off the job, demanding higher wages and better conditions. Production has ground to a halt.",
        "issue_type": "economic", "urgency": "high",
        "options": [
            {"id": 1, "text": "Grant wage increases. Meet worker demands.", "effects": {"stability": 0.05, "gdp_growth": -0.01, "unemployment": -0.02}, "flavor": "Workers return to work, morale high."},
            {"id": 2, "text": "Deploy police. Break up the strike by force.", "effects": {"stability": -0.08, "war_support": 0.03, "prestige": -5}, "flavor": "The strike is crushed, but resentment lingers."},
            {"id": 3, "text": "Negotiate a compromise deal with union leaders.", "effects": {"stability": 0.02, "gdp_growth": 0.005, "unemployment": -0.01}, "flavor": "A cautious settlement keeps the factories running."},
        ]
    },
    {
        "title": "Refugee Crisis at the Border",
        "description": "Thousands of displaced civilians are amassing at the border, fleeing conflict in a neighboring state. Local communities are overwhelmed.",
        "issue_type": "social", "urgency": "high",
        "options": [
            {"id": 1, "text": "Open the border. Accept refugees with full support.", "effects": {"stability": -0.03, "prestige": 8, "gdp_growth": 0.005}, "flavor": "International praise, but resources are strained."},
            {"id": 2, "text": "Close the border. Turn refugees away.", "effects": {"stability": 0.02, "prestige": -10, "war_support": 0.05}, "flavor": "Nationalists cheer, but the world condemns."},
            {"id": 3, "text": "Establish transit camps with international aid.", "effects": {"stability": 0.01, "prestige": 3, "gdp_growth": -0.005}, "flavor": "A measured response that satisfies no one fully."},
        ]
    },
    {
        "title": "Corruption Scandal Rocks Cabinet",
        "description": "Leaked documents reveal senior government officials have been accepting bribes from industrial corporations. Public trust in the government has collapsed.",
        "issue_type": "political", "urgency": "critical",
        "options": [
            {"id": 1, "text": "Launch a full public inquiry. Prosecute all officials.", "effects": {"stability": 0.08, "prestige": 10, "gdp_growth": -0.01}, "flavor": "Accountability restores public faith slowly."},
            {"id": 2, "text": "Cover it up. Dismiss the allegations as enemy propaganda.", "effects": {"stability": -0.1, "prestige": -15, "war_support": -0.05}, "flavor": "The cover-up leaks — things get worse."},
            {"id": 3, "text": "Quietly reassign the officials. Keep it out of the press.", "effects": {"stability": -0.02, "prestige": -5}, "flavor": "Bought time, but the problem festers."},
        ]
    },
    {
        "title": "Military Modernization Debate",
        "description": "The high command demands a new generation of weapons and equipment. The treasury warns the budget cannot sustain it without cuts elsewhere.",
        "issue_type": "military", "urgency": "normal",
        "options": [
            {"id": 1, "text": "Approve full military expansion. Raise military spending.", "effects": {"war_support": 0.08, "stability": -0.02, "gdp_growth": -0.015}, "flavor": "The army modernizes, but the economy strains."},
            {"id": 2, "text": "Reject the request. Prioritize domestic investment.", "effects": {"stability": 0.03, "gdp_growth": 0.01, "war_support": -0.05}, "flavor": "Generals are furious, but civilians applaud."},
            {"id": 3, "text": "Partial upgrade — modernize one branch only.", "effects": {"war_support": 0.03, "gdp_growth": -0.005}, "flavor": "A compromise that satisfies no one completely."},
        ]
    },
    {
        "title": "Economic Recession Looms",
        "description": "GDP growth has stalled and unemployment is rising. Economists warn of a potential recession if action is not taken immediately.",
        "issue_type": "economic", "urgency": "high",
        "options": [
            {"id": 1, "text": "Stimulus spending. Government invests heavily in infrastructure.", "effects": {"gdp_growth": 0.02, "unemployment": -0.03, "inflation": 0.02}, "flavor": "Growth returns, but prices rise."},
            {"id": 2, "text": "Austerity measures. Cut government spending drastically.", "effects": {"gdp_growth": -0.01, "stability": -0.05, "inflation": -0.01}, "flavor": "Budgets balance, but suffering increases."},
            {"id": 3, "text": "Encourage foreign investment with tax breaks.", "effects": {"gdp_growth": 0.015, "trade_openness": 0.05, "prestige": 3}, "flavor": "Foreign capital floods in, bringing growth."},
        ]
    },
    {
        "title": "Press Freedom Controversy",
        "description": "Opposition newspapers have been publishing articles highly critical of the government. Officials debate whether to restrict the press or allow free expression.",
        "issue_type": "political", "urgency": "normal",
        "options": [
            {"id": 1, "text": "Guarantee full press freedom. Criticism is protected.", "effects": {"stability": 0.04, "prestige": 8, "war_support": -0.03}, "flavor": "Democracy strengthened, but critics grow louder."},
            {"id": 2, "text": "Impose strict censorship. State controls the narrative.", "effects": {"stability": 0.02, "prestige": -12, "war_support": 0.05}, "flavor": "Dissent is silenced, but resentment grows underground."},
            {"id": 3, "text": "Regulate only content deemed 'harmful to national security'.", "effects": {"stability": 0.01, "prestige": -3}, "flavor": "A compromise that pleases few and angers many."},
        ]
    },
    {
        "title": "Agricultural Crisis",
        "description": "Poor harvests and drought have led to food shortages in rural regions. Food prices are rising in cities, causing unrest.",
        "issue_type": "social", "urgency": "high",
        "options": [
            {"id": 1, "text": "Emergency food imports. Buy from friendly nations.", "effects": {"stability": 0.05, "gdp_growth": -0.01, "prestige": 2}, "flavor": "Famine averted, but at economic cost."},
            {"id": 2, "text": "Nationalize food distribution. Ration supplies strictly.", "effects": {"stability": -0.02, "unemployment": 0.01, "war_support": -0.04}, "flavor": "Order maintained but morale drops."},
            {"id": 3, "text": "Invest in irrigation and modern farming technology.", "effects": {"gdp_growth": 0.01, "stability": 0.02, "unemployment": -0.01}, "flavor": "Long-term fix, but citizens suffer in the short term."},
        ]
    },
    {
        "title": "Territorial Dispute with Neighbor",
        "description": "A neighboring country has asserted historical claims over a disputed border region. Nationalist movements on both sides are escalating tensions.",
        "issue_type": "diplomatic", "urgency": "high",
        "options": [
            {"id": 1, "text": "Negotiate diplomatically. Seek international mediation.", "effects": {"stability": 0.03, "prestige": 5, "war_support": -0.04}, "flavor": "Peace preserved, nationalists feel betrayed."},
            {"id": 2, "text": "Mobilize troops to the border. Show military resolve.", "effects": {"war_support": 0.1, "stability": -0.03, "prestige": 3}, "flavor": "The nation rallies, but war grows closer."},
            {"id": 3, "text": "Demand binding arbitration through international courts.", "effects": {"prestige": 8, "stability": 0.02, "war_support": -0.02}, "flavor": "A peaceful but slow process begins."},
        ]
    },
    {
        "title": "Rail Network Overload",
        "description": "Freight rail lines are jammed as industry expands. Export delays are costing millions.",
        "issue_type": "economic", "urgency": "normal",
        "options": [
            {"id": 1, "text": "Fund new rail construction.", "effects": {"gdp_growth": 0.01, "stability": 0.01}, "flavor": "Construction booms; trade speeds up."},
            {"id": 2, "text": "Shift freight to trucks temporarily.", "effects": {"gdp_growth": 0.005, "inflation": 0.01}, "flavor": "Short-term relief, higher fuel costs."},
            {"id": 3, "text": "Impose export quotas until upgrades.", "effects": {"gdp_growth": -0.01, "stability": 0.02}, "flavor": "Domestic prices stabilize; exporters fume."},
        ]
    },
    {
        "title": "Border Smuggling Ring",
        "description": "Smugglers are moving fuel and weapons across the frontier, undermining state control.",
        "issue_type": "diplomatic", "urgency": "normal",
        "options": [
            {"id": 1, "text": "Launch a crackdown operation.", "effects": {"stability": 0.02, "prestige": 3}, "flavor": "Seizures rise; corruption investigations follow."},
            {"id": 2, "text": "Negotiate joint patrols with neighbor.", "effects": {"prestige": 5, "stability": 0.01}, "flavor": "Cooperation improves relations."},
            {"id": 3, "text": "Quietly tolerate for now.", "effects": {"stability": -0.02, "gdp_growth": 0.005}, "flavor": "Black market expands."},
        ]
    },
    {
        "title": "Veterans Demand Benefits",
        "description": "War veterans are protesting in the capital, demanding expanded support and pensions.",
        "issue_type": "social", "urgency": "high",
        "options": [
            {"id": 1, "text": "Expand benefits immediately.", "effects": {"happiness": 0.04, "stability": 0.03, "gdp_growth": -0.01}, "flavor": "Public support rises; budget tightens."},
            {"id": 2, "text": "Offer phased reforms.", "effects": {"happiness": 0.02, "stability": 0.01}, "flavor": "Some appeased; protests continue."},
            {"id": 3, "text": "Refuse new spending.", "effects": {"happiness": -0.04, "stability": -0.03}, "flavor": "Demonstrations spread."},
        ]
    },
    {
        "title": "Arms Factory Accident",
        "description": "An explosion at a major arms plant halts production and sparks safety protests.",
        "issue_type": "military", "urgency": "high",
        "options": [
            {"id": 1, "text": "Invest in safety upgrades.", "effects": {"stability": 0.02, "gdp_growth": -0.005}, "flavor": "Output recovers slowly but safely."},
            {"id": 2, "text": "Press production at all costs.", "effects": {"war_support": 0.03, "stability": -0.03}, "flavor": "Output rises, unrest grows."},
            {"id": 3, "text": "Shift to private contractors.", "effects": {"gdp_growth": 0.004, "prestige": -2}, "flavor": "Costs fall; oversight weakens."},
        ]
    },
    {
        "title": "Currency Shock",
        "description": "Foreign investors are dumping the national currency. Inflation fears are rising.",
        "issue_type": "economic", "urgency": "high",
        "options": [
            {"id": 1, "text": "Raise interest rates sharply.", "effects": {"inflation": -0.01, "gdp_growth": -0.01}, "flavor": "Currency stabilizes; growth slows."},
            {"id": 2, "text": "Impose capital controls.", "effects": {"stability": 0.02, "prestige": -4}, "flavor": "Markets calm, reputation suffers."},
            {"id": 3, "text": "Let the currency float.", "effects": {"gdp_growth": 0.005, "inflation": 0.01}, "flavor": "Exports surge, prices rise."},
        ]
    },
    {
        "title": "Cybersecurity Breach",
        "description": "A major data breach hits government systems, exposing citizen records.",
        "issue_type": "political", "urgency": "high",
        "options": [
            {"id": 1, "text": "Create a national cyber agency.", "effects": {"stability": 0.02, "prestige": 4, "gdp_growth": -0.005}, "flavor": "Security improves over time."},
            {"id": 2, "text": "Outsource to private firms.", "effects": {"prestige": 2, "gdp_growth": 0.003}, "flavor": "Fast response; accountability debated."},
            {"id": 3, "text": "Downplay and move on.", "effects": {"stability": -0.03, "prestige": -5}, "flavor": "Public trust erodes."},
        ]
    },
]
_issue_index = 0


async def generate_issues(player_nation: dict, turn: int, recent_events: list[str], hint: str = "") -> list[dict]:
    """Try AI first, fall back to curated pool if AI is too slow."""
    global _issue_index
    name = player_nation.get('name', '')
    ideology = player_nation.get('ideology', '')
    year = player_nation.get('year', 1936)

    type_clause = f" Focus on {hint} issues." if hint else ""
    msg = (
        f"/no_think {name} ({ideology}, {year}) strategy game policy issue.{type_clause} "
        f"Max 20-word description. Max 8-word option texts. "
        f'Format exactly: {{"title":"X","description":"X","issue_type":"economic","urgency":"high",'
        f'"options":[{{"id":1,"text":"X","effects":{{"stability":0.05}},"flavor":"X"}},'
        f'{{"id":2,"text":"X","effects":{{"stability":-0.05}},"flavor":"X"}},'
        f'{{"id":3,"text":"X","effects":{{"gdp_growth":0.02}},"flavor":"X"}}]}}'
    )
    try:
        if not AI_ENABLED:
            raise RuntimeError("AI disabled")
        raw = await _call_ai([{"role": "user", "content": msg}], temperature=0.8, max_tokens=600, prefill='{"title":"')
        result = _extract_json(raw)
        if isinstance(result, dict) and "title" in result and result.get("options"):
            print(f"AI issue generated: {result['title']}")
            return [result]
        if isinstance(result, list) and result and isinstance(result[0], dict) and "title" in result[0]:
            return [result[0]]
        print(f"AI issue JSON invalid, using fallback. Raw: {repr(raw[:100])}")
    except Exception as e:
        print(f"AI issue timeout — using fallback ({type(e).__name__})")

    # Fallback: pick from curated pool, cycling through them
    issue = dict(_FALLBACK_ISSUES[_issue_index % len(_FALLBACK_ISSUES)])
    _issue_index += 1
    return [issue]


# ── Diplomacy ────────────────────────────────────────────────────────────────

async def generate_diplomatic_response(
    target_nation: dict, player_nation: dict, action_type: str, details: dict
) -> dict:
    rel = target_nation.get('diplomacy', {}).get('relations', {}).get(player_nation.get('name', ''), 0)
    ideology_match = target_nation.get('ideology') == player_nation.get('ideology')

    msg = (
        f"/no_think {target_nation.get('name')}({target_nation.get('ideology')}) "
        f"relation with {player_nation.get('name')}:{rel}. "
        f"Proposal:{action_type}. "
        f'Return ONLY JSON: {{"accepted":true,"response_message":"One sentence.","relation_change":5,"counteroffer":null}}'
    )
    try:
        if not AI_ENABLED:
            from backend import npc_rules
            return npc_rules.diplomatic_response(
                target_nation, player_nation, action_type, details,
                world_tension=player_nation.get("world_tension", 0.0)
            )
        if not AI_ENABLED:
            raise RuntimeError("AI disabled")
        raw = await _call_ai([{"role": "user", "content": msg}], temperature=0.6, max_tokens=600, prefill='{"accepted":')
        result = _extract_json(raw)
        if result and "accepted" in result:
            return result
    except Exception as e:
        print(f"AI diplomacy fallback ({type(e).__name__})")

    # Fallback: decide based on relations
    accepted = rel > 20 or (ideology_match and rel > -10)
    counteroffer = None
    if not accepted:
        if action_type == "form_alliance":
            counteroffer = "We might consider a trade deal or defense pact instead."
        elif action_type == "defense_pact":
            counteroffer = "Perhaps we could begin with a trade agreement to build trust."
    return {
        "accepted": accepted,
        "response_message": f"{target_nation.get('name')} {'agrees to' if accepted else 'declines'} the {action_type.replace('_', ' ')} proposal.",
        "relation_change": 5 if accepted else -3,
        "counteroffer": counteroffer,
    }


# ── War / Peace ───────────────────────────────────────────────────────────────

async def generate_war_events(attacker: dict, defender: dict, war: dict) -> dict:
    msg = (
        f"/no_think War:{attacker.get('name')} vs {defender.get('name')}. "
        f"Warscore:{war.get('attacker_warscore',0):.0f}. "
        f'Return ONLY JSON: {{"battle_result":"attacker_victory","warscore_change":5,'
        f'"attacker_losses":8000,"defender_losses":12000,"headline":"Battle name","event_description":"One sentence."}}'
    )
    try:
        if not AI_ENABLED:
            raise RuntimeError("AI disabled")
        raw = await _call_ai([{"role": "user", "content": msg}], temperature=0.7, max_tokens=600)
        result = _extract_json(raw)
        if result:
            return result
    except Exception:
        pass
    return {
        "battle_result": "stalemate", "warscore_change": 0,
        "attacker_losses": 5000, "defender_losses": 5000,
        "headline": "Fierce fighting at the front", "event_description": "Forces remain locked in brutal combat."
    }


async def generate_peace_terms(winner: dict, loser: dict, warscore: float) -> dict:
    # Always return static terms instantly — no AI needed here
    loser_name = loser.get('name', 'the enemy')
    return {
        "available_terms": [
            {"id": "annex", "label": "Full Annexation", "description": f"Completely absorb {loser_name} into your nation.", "cost_warscore": 100, "effects": {"prestige": 20, "stability_change": -0.1}},
            {"id": "puppet", "label": "Install Puppet Government", "description": f"Install a loyal regime in {loser_name}.", "cost_warscore": 60, "effects": {"prestige": 10, "stability_change": -0.05}},
            {"id": "reparations", "label": "Demand Reparations", "description": "Extract war payments and resources.", "cost_warscore": 30, "effects": {"gdp_change": 20, "prestige": 5}},
            {"id": "status_quo", "label": "White Peace", "description": "Return to pre-war borders. No gains.", "cost_warscore": 0, "effects": {"prestige": -5}},
        ],
        "flavor_text": f"{loser_name} lies defeated, awaiting your judgement."
    }


# ── News ──────────────────────────────────────────────────────────────────────

async def generate_news_headline(event_type: str, context: dict) -> str:
    msg = (
        f"/no_think 8-word newspaper headline for: {event_type}. "
        f"{context.get('attacker','')} {context.get('defender','')}. Return only the headline."
    )
    try:
        if not AI_ENABLED:
            raise RuntimeError("AI disabled")
        raw = await _call_ai([{"role": "user", "content": msg}], temperature=0.9, max_tokens=500)
        raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip().strip('"').strip("'")
        if raw and len(raw) < 150:
            return raw
    except Exception:
        pass
    templates = {
        "war_declared": f"{context.get('attacker','')} Declares War on {context.get('defender','')}",
        "alliance_formed": "Historic Alliance Signed Between Nations",
        "peace_signed": "Peace Treaty Ends Conflict",
        "sanctions": "Economic Sanctions Imposed",
    }
    return templates.get(event_type, event_type.replace("_", " ").title())


# ── Starter Content ──────────────────────────────────────────────────────────

async def _generate_typed_issue(era_name: str, ideology: str, year: int, itype: str) -> dict | None:
    msg = (
        f"/no_think {ideology} nation, {era_name} ({year}), {itype} issue. "
        f"Max 20-word description, max 8-word option texts. "
        f'Format: {{"title":"X","description":"X","issue_type":"{itype}","urgency":"normal",'
        f'"options":[{{"id":1,"text":"X","effects":{{"stability":0.05,"happiness":0.03}},"flavor":"X"}},'
        f'{{"id":2,"text":"X","effects":{{"stability":-0.05,"happiness":-0.04}},"flavor":"X"}},'
        f'{{"id":3,"text":"X","effects":{{"gdp_growth":0.02,"happiness":0.01}},"flavor":"X"}}]}}'
    )
    try:
        raw = await _call_ai([{"role": "user", "content": msg}], temperature=0.85, max_tokens=600, prefill='{"title":"')
        result = _extract_json(raw)
        if isinstance(result, dict) and "title" in result and result.get("options"):
            return result
    except Exception:
        pass
    return None


async def generate_starter_issues(era_name: str, ideology: str, year: int) -> list[dict]:
    """Generate one issue per type in parallel — called once at game start to pre-fill the pool."""
    if not AI_ENABLED:
        return []
    types = ["economic", "political", "social", "military", "diplomatic"]
    tasks = [_generate_typed_issue(era_name, ideology, year, t) for t in types]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if isinstance(r, dict) and "title" in r]


async def generate_starter_news(era_name: str, player_nation: str, year: int) -> list[str]:
    """Generate 8 world-news headlines at game start to populate the news ticker."""
    msg = (
        f"/no_think 8 newspaper headlines for {era_name} ({year}). "
        f"Mix of politics, economy, military, diplomacy from different world regions. "
        f"Each headline max 10 words. "
        f'Return ONLY JSON array: ["Headline 1","Headline 2",...]'
    )
    try:
        if not AI_ENABLED:
            raise RuntimeError("AI disabled")
        raw = await _call_ai([{"role": "user", "content": msg}], temperature=0.9, max_tokens=600, prefill='["')
        result = _extract_json(raw)
        if isinstance(result, list) and result and isinstance(result[0], str):
            return [h for h in result if isinstance(h, str)][:8]
    except Exception:
        pass
    # Static fallbacks for quick startup
    return [
        f"World Leaders Gather for {era_name} Summit",
        "Economic Growth Continues Amid Global Uncertainty",
        "Military Modernization Programs Accelerate Worldwide",
        "Diplomatic Tensions Rise Over Disputed Territories",
        "New Trade Routes Open Between Eastern Nations",
        "Scientists Announce Major Industrial Breakthrough",
        "Refugee Crisis Strains International Aid Networks",
        "Naval Powers Contest Strategic Waterway Control",
    ]


async def generate_resource_trade_response(
    target_nation: dict, player_nation: dict,
    offer_resource: str, offer_amount: float,
    request_resource: str, request_amount: float
) -> dict:
    rel = target_nation.get("diplomacy", {}).get("relations", {}).get(player_nation.get("name", ""), 0)
    msg = (
        f"/no_think {target_nation.get('name')} evaluates trade from {player_nation.get('name')}. "
        f"Offer: {offer_amount} {offer_resource}/turn. Want: {request_amount} {request_resource}/turn. "
        f"Relations: {rel}. "
        f'Return ONLY JSON: {{"accepted":true,"response_message":"One sentence.","counteroffer":null}}'
    )
    try:
        if not AI_ENABLED:
            from backend import npc_rules
            return npc_rules.resource_trade_response(
                target_nation, player_nation, offer_amount, request_amount
            )
        if not AI_ENABLED:
            raise RuntimeError("AI disabled")
        raw = await _call_ai([{"role": "user", "content": msg}], temperature=0.6, max_tokens=400, prefill='{"accepted":')
        result = _extract_json(raw)
        if result and "accepted" in result:
            return result
    except Exception:
        pass
    accepted = rel > 10
    return {
        "accepted": accepted,
        "response_message": f"{target_nation.get('name')} {'agrees to' if accepted else 'declines'} the resource trade.",
        "counteroffer": None
    }


async def generate_troop_request_response(
    target_nation: dict, player_nation: dict, war_id: str, troops_requested: int
) -> dict:
    rel = target_nation.get("diplomacy", {}).get("relations", {}).get(player_nation.get("name", ""), 0)
    is_ally = player_nation.get("name", "") in str(target_nation.get("diplomacy", {}).get("alliances", []))
    msg = (
        f"/no_think {target_nation.get('name')} considers sending {troops_requested:,} troops to help "
        f"{player_nation.get('name')}. Alliance: {is_ally}. Relations: {rel}. "
        f'Return ONLY JSON: {{"accepted":true,"troops_sent":5000,"response_message":"One sentence."}}'
    )
    try:
        if not AI_ENABLED:
            from backend import npc_rules
            return npc_rules.troop_request_response(
                target_nation, player_nation, war_id, troops_requested
            )
        if not AI_ENABLED:
            raise RuntimeError("AI disabled")
        raw = await _call_ai([{"role": "user", "content": msg}], temperature=0.6, max_tokens=400, prefill='{"accepted":')
        result = _extract_json(raw)
        if result and "accepted" in result:
            return result
    except Exception:
        pass
    accepted = is_ally or rel > 40
    troops_sent = min(troops_requested, target_nation.get("military", {}).get("army_size", 0) // 5) if accepted else 0
    return {
        "accepted": accepted,
        "troops_sent": troops_sent,
        "response_message": f"{target_nation.get('name')} {'sends reinforcements' if accepted else 'declines to commit troops'}."
    }


async def generate_tech_purchase_response(
    target_nation: dict, player_nation: dict, tech_branch: str, price_gdp: float
) -> dict:
    rel = target_nation.get("diplomacy", {}).get("relations", {}).get(player_nation.get("name", ""), 0)
    msg = (
        f"/no_think {target_nation.get('name')} considers selling {tech_branch} technology to "
        f"{player_nation.get('name')} for {price_gdp:.0f}B GDP. Relations: {rel}. "
        f'Return ONLY JSON: {{"accepted":true,"response_message":"One sentence."}}'
    )
    try:
        if not AI_ENABLED:
            from backend import npc_rules
            return npc_rules.tech_purchase_response(
                target_nation, player_nation, price_gdp
            )
        if not AI_ENABLED:
            raise RuntimeError("AI disabled")
        raw = await _call_ai([{"role": "user", "content": msg}], temperature=0.6, max_tokens=300, prefill='{"accepted":')
        result = _extract_json(raw)
        if result and "accepted" in result:
            return result
    except Exception:
        pass
    accepted = rel > 30
    return {
        "accepted": accepted,
        "response_message": f"{target_nation.get('name')} {'agrees to transfer' if accepted else 'refuses to share'} {tech_branch} technology."
    }


async def generate_joint_research_response(
    target_nation: dict, player_nation: dict, tech_branch: str
) -> dict:
    rel = target_nation.get("diplomacy", {}).get("relations", {}).get(player_nation.get("name", ""), 0)
    msg = (
        f"/no_think {target_nation.get('name')} evaluates joint {tech_branch} research with "
        f"{player_nation.get('name')}. Relations: {rel}. "
        f'Return ONLY JSON: {{"accepted":true,"response_message":"One sentence."}}'
    )
    try:
        if not AI_ENABLED:
            from backend import npc_rules
            return npc_rules.joint_research_response(target_nation, player_nation)
        if not AI_ENABLED:
            raise RuntimeError("AI disabled")
        raw = await _call_ai([{"role": "user", "content": msg}], temperature=0.6, max_tokens=300, prefill='{"accepted":')
        result = _extract_json(raw)
        if result and "accepted" in result:
            return result
    except Exception:
        pass
    accepted = rel > 20
    return {
        "accepted": accepted,
        "response_message": f"{target_nation.get('name')} {'joins' if accepted else 'declines'} the joint {tech_branch} research program."
    }


# ── Status ────────────────────────────────────────────────────────────────────

async def check_ai_server() -> dict:
    if not AI_ENABLED:
        return {"status": "offline", "error": "AI disabled", "url": AI_BASE_URL}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{AI_BASE_URL}/models")
            data = r.json()
            models = [m["id"] for m in data.get("data", [])]
            return {"status": "online", "models": models, "url": AI_BASE_URL}
    except Exception as e:
        return {"status": "offline", "error": str(e), "url": AI_BASE_URL}
