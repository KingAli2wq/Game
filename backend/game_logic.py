import asyncio
import random
import math
from backend.models import GameState, Nation, War, Issue, IssueOption
from backend import ai_engine


MAX_PENDING_ISSUES = 4


IDEOLOGY_COLORS = {
    "Liberal Democracy": "#3b82f6",
    "Social Democracy": "#22c55e",
    "Conservative Democracy": "#f59e0b",
    "Socialism": "#ef4444",
    "Communism": "#dc2626",
    "Fascism": "#1c1917",
    "Monarchy": "#7c3aed",
    "Theocracy": "#059669",
    "Technocracy": "#0ea5e9",
    "Oligarchy": "#78716c",
}

IDEOLOGY_AGGRESSION = {
    "Liberal Democracy": -0.3, "Social Democracy": -0.2, "Conservative Democracy": -0.1,
    "Socialism": 0.0, "Communism": 0.1, "Fascism": 0.4,
    "Monarchy": 0.1, "Theocracy": 0.15, "Technocracy": -0.1, "Oligarchy": 0.05,
}

# Ideologies that face diplomatic pressure from democratic nations
AUTHORITARIAN_IDEOLOGIES = {"Fascism", "Communism", "Oligarchy"}
DEMOCRATIC_IDEOLOGIES = {"Liberal Democracy", "Social Democracy", "Conservative Democracy"}


def simulate_economy(nation: Nation) -> Nation:
    eco = nation.economy
    mil = nation.military

    growth = eco.gdp_growth
    growth += (eco.trade_openness - 0.5) * 0.02
    growth -= eco.nationalization * 0.015
    growth += (eco.gov_spending - 0.3) * 0.01

    # Tech bonus: industry level above 1 adds a small growth multiplier
    industry_tech = nation.tech_levels.get("industry", 1)
    growth += (industry_tech - 1) * 0.003

    mil_burden = mil.military_spending
    growth -= max(0, mil_burden - 0.05) * 0.3
    eco.inflation += max(0, mil_burden - 0.08) * 0.02

    growth *= (0.5 + nation.stability * 0.5)

    eco.gdp = max(1.0, eco.gdp * (1 + growth * 0.083))
    eco.gdp_growth = max(-0.1, min(0.15, growth))

    if growth > 0.03:
        eco.unemployment = max(0.02, eco.unemployment - 0.003)
    elif growth < 0:
        eco.unemployment = min(0.35, eco.unemployment + 0.005)

    eco.inflation = max(0.0, min(0.5, eco.inflation * 0.98 + eco.gov_spending * 0.005))
    eco.trade_balance = (eco.trade_openness - 0.5) * 20 + random.gauss(0, 3)
    eco.industry_output = eco.gdp * 0.35 * (0.5 + eco.trade_openness * 0.5)

    # Resource production: each lab/factory contributes to processed stockpile
    steel_prod = (eco.resources.get("iron_ore", 0) * 0.05 + eco.factories * 0.5)
    fuel_prod = eco.resources.get("oil", 0) * 0.08
    equip_prod = eco.arms_factories * 1.5 * (0.5 + mil.equipment_level * 0.5)
    eco.stockpile["steel"] = min(2000, eco.stockpile.get("steel", 100) + steel_prod * 0.1)
    eco.stockpile["fuel"] = min(2000, eco.stockpile.get("fuel", 100) + fuel_prod * 0.1)
    eco.stockpile["equipment"] = min(1000, eco.stockpile.get("equipment", 50) + equip_prod * 0.1)

    # Military consumes equipment and fuel when at war
    if nation.is_at_war:
        eco.stockpile["equipment"] = max(0, eco.stockpile.get("equipment", 0) - mil.army_size * 0.0001)
        eco.stockpile["fuel"] = max(0, eco.stockpile.get("fuel", 0) - 5)

    nation.economy = eco
    return nation


def simulate_happiness(nation: Nation) -> Nation:
    """Update citizen happiness based on economic and political conditions."""
    eco = nation.economy
    target = 0.5  # baseline

    # Economy: good growth and low unemployment boost happiness
    target += eco.gdp_growth * 2.0
    target -= max(0, eco.unemployment - 0.07) * 1.5
    target -= max(0, eco.inflation - 0.05) * 1.0

    # Stability and war
    target += (nation.stability - 0.5) * 0.4
    if nation.is_at_war:
        target += (nation.war_support - 0.5) * 0.3
        target -= 0.05  # war is always stressful

    # Government spending on welfare improves happiness
    target += (eco.gov_spending - 0.3) * 0.2

    target = max(0.0, min(1.0, target))
    # Happiness moves slowly toward target (inertia)
    nation.happiness = max(0.0, min(1.0, nation.happiness + (target - nation.happiness) * 0.15))

    # Very low happiness destabilizes the nation
    if nation.happiness < 0.3:
        nation.stability = max(0.05, nation.stability - 0.01)

    return nation


def simulate_political_power(nation: Nation) -> Nation:
    """Accumulate political power each month based on stability and prestige."""
    base = 2.0
    stability_bonus = max(0.0, nation.stability - 0.4) * 4.0
    prestige_bonus = min(1.5, nation.prestige / 100.0)
    gain = base + stability_bonus + prestige_bonus
    nation.political_power = max(0.0, min(300.0, nation.political_power + gain))
    return nation


def simulate_research(nation: Nation) -> Nation:
    """Legacy research points — kept for backward compatibility."""
    labs = nation.economy.research_labs
    base_rp = labs * 1.0 * (0.5 + nation.stability * 0.5)
    nation.research_points += base_rp
    return nation


def advance_research_projects(nation: Nation, days_per_month: int = 30) -> Nation:
    """Advance active research projects based on daily research speed."""
    if not nation.research_projects:
        return nation

    from backend.tech_nodes import get_node, apply_node_unlocks, can_research

    # Simple daily speed: labs + stability bonus
    labs = nation.economy.research_labs
    daily_speed = max(0.2, 1.0 + (labs * 0.2) + (nation.stability * 0.5))
    researched = set(nation.tech_levels.get("researched_nodes", []))

    completed = []
    for proj in nation.research_projects:
        node = get_node(proj.node_id)
        if not node:
            completed.append(proj)
            continue
        # If prereqs no longer valid, pause by skipping progress
        ok, _ = can_research(proj.node_id, researched)
        if not ok and proj.node_id not in researched:
            continue

        proj.total_days = node.get("days", proj.total_days or 60)
        proj.progress_days += daily_speed * days_per_month
        if proj.progress_days >= proj.total_days:
            completed.append(proj)

    for proj in completed:
        node = get_node(proj.node_id)
        if node and proj.node_id not in researched:
            researched.add(proj.node_id)
            nation.tech_levels["researched_nodes"] = list(researched)
            # Apply unlocks to the nation model via dict merge
            nation_data = nation.model_dump()
            nation_data = apply_node_unlocks(nation_data, node)
            nation = Nation.model_validate(nation_data)
        nation.research_projects = [p for p in nation.research_projects if p.node_id != proj.node_id]

    return nation


def simulate_military_growth(nation: Nation) -> Nation:
    mil = nation.military
    eco = nation.economy

    mil.manpower_pool = min(int(nation.population * 0.15), mil.manpower_pool + int(nation.population * 0.001))
    mil.equipment_level = min(1.0, mil.equipment_level + eco.industry_output * 0.0002)

    if nation.is_at_war:
        mil.morale = min(1.0, mil.morale + nation.war_support * 0.02 - 0.01)
    else:
        mil.morale = min(1.0, mil.morale + 0.005)

    nation.military = mil
    return nation


def calculate_combat_power(nation: Nation) -> float:
    mil = nation.military
    base = mil.army_size * mil.equipment_level * mil.morale
    tech_bonus = 1 + (mil.equipment_level - 0.5) * 0.4
    return base * tech_bonus


def resolve_combat_turn(state: GameState, war: War) -> tuple[War, list[str]]:
    logs = []
    attacker = state.nations.get(war.attacker)
    defender = state.nations.get(war.defender)
    if not attacker or not defender:
        return war, logs

    att_power = calculate_combat_power(attacker)
    def_power = calculate_combat_power(defender)

    for ally_id in war.attacker_allies:
        ally = state.nations.get(ally_id)
        if ally:
            att_power += calculate_combat_power(ally) * 0.6

    for ally_id in war.defender_allies:
        ally = state.nations.get(ally_id)
        if ally:
            def_power += calculate_combat_power(ally) * 0.6

    ratio = att_power / max(def_power, 1)
    base_change = (ratio - 1) * 5 + random.gauss(0, 3)
    warscore_change = max(-10, min(12, base_change))

    war.attacker_warscore = max(-100, min(100, war.attacker_warscore + warscore_change))

    att_losses = int(random.uniform(1000, 15000) * (def_power / max(att_power, 1)) * 0.3)
    def_losses = int(random.uniform(1000, 15000) * (att_power / max(def_power, 1)) * 0.3)

    attacker.military.army_size = max(0, attacker.military.army_size - att_losses)
    defender.military.army_size = max(0, defender.military.army_size - def_losses)
    attacker.military.morale = max(0.1, attacker.military.morale - att_losses / max(attacker.military.army_size, 1) * 0.1)
    defender.military.morale = max(0.1, defender.military.morale - def_losses / max(defender.military.army_size, 1) * 0.1)

    state.nations[war.attacker] = attacker
    state.nations[war.defender] = defender

    direction = "gaining ground" if warscore_change > 0 else "losing ground"
    logs.append(f"{attacker.name} is {direction} against {defender.name} (warscore: {war.attacker_warscore:.1f})")

    if war.attacker_warscore >= 100:
        war.status = "attacker_won"
        logs.append(f"{attacker.name} has won the war against {defender.name}!")
    elif war.attacker_warscore <= -100:
        war.status = "defender_won"
        logs.append(f"{defender.name} has repelled {attacker.name}'s invasion!")
    elif defender.military.army_size < 5000:
        war.status = "attacker_won"
        war.attacker_warscore = 100
        logs.append(f"{defender.name}'s military has collapsed! {attacker.name} wins!")

    return war, logs


def apply_stability_effects(nation: Nation) -> Nation:
    eco = nation.economy
    stability_delta = 0.0
    if eco.unemployment > 0.15:
        stability_delta -= (eco.unemployment - 0.15) * 0.3
    if eco.inflation > 0.1:
        stability_delta -= (eco.inflation - 0.1) * 0.2
    if eco.gdp_growth > 0.04:
        stability_delta += 0.01
    nation.stability = max(0.05, min(1.0, nation.stability + stability_delta * 0.1))
    return nation


def apply_issue_effects(state: GameState, issue: Issue, option_id: int) -> tuple[GameState, str]:
    option = next((o for o in issue.options if o.id == option_id), None)
    if not option:
        return state, "Invalid option"

    player = state.get_player_nation()
    if not player:
        return state, "No player nation"

    effects = option.effects
    eco = player.economy

    # Core nation stats
    player.stability = max(0.0, min(1.0, player.stability + effects.get("stability", 0)))
    player.war_support = max(0.0, min(1.0, player.war_support + effects.get("war_support", 0)))
    player.prestige = max(0, min(200, player.prestige + effects.get("prestige", 0)))
    player.happiness = max(0.0, min(1.0, player.happiness + effects.get("happiness", 0)))
    player.population = max(1_000, player.population + effects.get("population", 0))

    # Economy
    eco.gdp_growth = max(-0.1, min(0.15, eco.gdp_growth + effects.get("gdp_growth", 0)))
    eco.unemployment = max(0.01, min(0.5, eco.unemployment + effects.get("unemployment", 0)))
    eco.inflation = max(0.0, min(0.5, eco.inflation + effects.get("inflation", 0)))
    eco.trade_openness = max(0.0, min(1.0, eco.trade_openness + effects.get("trade_openness", 0)))

    # Industry & research
    eco.factories = max(1, eco.factories + effects.get("factories", 0))
    eco.arms_factories = max(0, eco.arms_factories + effects.get("arms_factories", 0))
    eco.research_labs = max(0, eco.research_labs + effects.get("research_labs", 0))
    player.research_points += effects.get("research_points", 0)

    # Tech level direct boost (from buying/gifting tech)
    tech_boost = effects.get("tech_boost", {})
    for branch, amount in tech_boost.items():
        current = player.tech_levels.get(branch, 1)
        player.tech_levels[branch] = min(10, current + amount)

    # Stockpile gains/losses (e.g. "stockpile.steel": 50)
    for key, val in effects.items():
        if key.startswith("stockpile."):
            resource = key.split(".", 1)[1]
            eco.stockpile[resource] = max(0, eco.stockpile.get(resource, 0) + val)

    # Military
    mil = player.military
    mil.army_size = max(0, mil.army_size + effects.get("army_size", 0))
    mil.morale = max(0.0, min(1.0, mil.morale + effects.get("morale", 0)))
    mil.equipment_level = max(0.1, min(1.0, mil.equipment_level + effects.get("equipment_level", 0)))

    # World tension
    state.world_tension = max(0.0, min(1.0, state.world_tension + effects.get("world_tension", 0)))

    # Relations with other nations
    relations_change = effects.get("relations_change", {})
    for nation_id, change in relations_change.items():
        for nid, n in state.nations.items():
            if n.name == nation_id or nid == nation_id:
                current = player.diplomacy.relations.get(nid, 0)
                player.diplomacy.relations[nid] = max(-100, min(100, current + change))
                other_current = n.diplomacy.relations.get(state.player_nation_id, 0)
                n.diplomacy.relations[state.player_nation_id] = max(-100, min(100, other_current + change * 0.5))
                state.nations[nid] = n

    player.economy = eco
    player.military = mil
    state.nations[state.player_nation_id] = player
    issue.resolved = True
    issue.chosen_option = option_id

    # Publish the option's news headline to the news feed
    news_headline = option.news
    if not news_headline:
        # Fallback generic headline
        news_headline = f"{player.name}: {issue.title} — Decision Made"
    state.add_news(news_headline, state.player_nation_id, issue.issue_type)

    flavor = option.flavor or "The policy has been implemented."
    return state, flavor


def apply_policy_effects(nation: Nation) -> Nation:
    """Apply per-turn effects of all active policies."""
    if not nation.active_policies:
        return nation
    from backend.policies_library import get_policy
    eco = nation.economy
    for policy_id in nation.active_policies:
        policy = get_policy(policy_id)
        if not policy:
            continue
        if policy.get("requires_at_war") and not nation.is_at_war:
            continue
        for key, val in policy.get("effects", {}).items():
            if key == "gdp_growth":
                eco.gdp_growth = min(0.15, max(-0.1, eco.gdp_growth + val))
            elif key == "stability":
                nation.stability = min(1.0, max(0.0, nation.stability + val))
            elif key == "happiness":
                nation.happiness = min(1.0, max(0.0, nation.happiness + val))
            elif key == "war_support":
                nation.war_support = min(1.0, max(0.0, nation.war_support + val))
            elif key == "inflation":
                eco.inflation = min(0.5, max(0.0, eco.inflation + val))
            elif key == "research_points":
                nation.research_points = max(0.0, nation.research_points + val)
            elif key == "prestige":
                nation.prestige = max(0, nation.prestige + val)
            elif key == "unemployment":
                eco.unemployment = min(0.35, max(0.01, eco.unemployment + val))
    nation.economy = eco
    return nation


def _make_rule_based_decision(state: GameState, nation_id: str) -> dict:
    """Fast decision for low-priority nations — no AI call needed."""
    nation = state.nations[nation_id]
    eco = nation.economy
    mil = nation.military
    agg = nation.personality.aggression

    # Weight each action based on current stats
    w_economy = max(0.0, 0.5 - eco.gdp_growth * 8)
    w_army = max(0.0, (agg - 0.3) * 0.6) if mil.army_size < 300_000 else 0.0
    w_diplo = max(0.0, 0.4 - agg * 0.3)
    total = w_economy + w_army + w_diplo or 1.0

    r = random.random() * total
    if r < w_economy:
        return {"actions": [{"action": "boost_economy", "target": None, "reason": "stimulating growth"}]}
    elif r < w_economy + w_army:
        return {"actions": [{"action": "build_army", "target": None, "reason": "military expansion"}]}
    else:
        # Pick the alive non-player nation with the highest current relation to improve with
        best_name = None
        best_rel = -200
        for nid, n in state.nations.items():
            if nid == nation_id or nid == state.player_nation_id or not n.is_alive:
                continue
            rel = nation.diplomacy.relations.get(nid, 0)
            if rel > best_rel and rel < 80:
                best_rel = rel
                best_name = n.name
        return {"actions": [{"action": "improve_relations", "target": best_name, "reason": "building ties"}]}


async def process_ai_turns(state: GameState, broadcast_fn=None) -> tuple[GameState, list[str]]:
    logs = []
    game_summary = build_game_summary(state)

    # Hard cap on AI calls per turn to keep turn times reasonable.
    max_ai_calls = 2

    npc_ids = [nid for nid, n in state.nations.items()
               if nid != state.player_nation_id and n.is_alive]

    # High-priority nations (aggressive or high world tension) get real AI calls.
    # Everything else uses fast rule-based logic — cuts AI calls from N → 2-3.
    ai_ids, rule_ids = [], []
    for nid in npc_ids:
        n = state.nations[nid]
        if n.personality.aggression > 0.65 or state.world_tension > 0.55:
            ai_ids.append(nid)
        else:
            rule_ids.append(nid)

    if len(ai_ids) > max_ai_calls:
        ai_ids = sorted(
            ai_ids,
            key=lambda nid: state.nations[nid].personality.aggression,
            reverse=True
        )[:max_ai_calls]
        rule_ids = [nid for nid in npc_ids if nid not in ai_ids]

    # Fire ALL AI calls simultaneously instead of sequentially.
    # 9 sequential × 15s = 135s  →  parallel = ~15s (time of slowest call).
    ai_tasks = [ai_engine.generate_nation_decision(game_summary, nid) for nid in ai_ids]
    ai_results = await asyncio.gather(*ai_tasks, return_exceptions=True)

    all_decisions: list[tuple[str, dict]] = []
    for nid, result in zip(ai_ids, ai_results):
        dec = {"actions": []} if isinstance(result, Exception) else result
        all_decisions.append((nid, dec))
    for nid in rule_ids:
        all_decisions.append((nid, _make_rule_based_decision(state, nid)))

    # Apply all decisions sequentially (state is shared — can't mutate in parallel)
    for nation_id, decision in all_decisions:
        nation = state.nations.get(nation_id)
        if not nation:
            continue
        try:
            actions = decision.get("actions", [])
            for action in actions[:2]:
                action_type = action.get("action", "")
                target_name = action.get("target", "")

                if action_type == "improve_relations" and target_name:
                    target_id = find_nation_id(state, target_name)
                    if target_id and target_id != nation_id:
                        current = nation.diplomacy.relations.get(target_id, 0)
                        nation.diplomacy.relations[target_id] = min(100, current + random.randint(3, 8))
                        target = state.nations[target_id]
                        target.diplomacy.relations[nation_id] = min(100, target.diplomacy.relations.get(nation_id, 0) + random.randint(2, 5))
                        state.nations[target_id] = target
                        log_msg = f"{nation.name} improves relations with {target.name}"
                        logs.append(log_msg)
                        if broadcast_fn:
                            await broadcast_fn({"type": "turn_action", "message": log_msg, "action_type": "diplomacy"})

                elif action_type == "form_alliance" and target_name:
                    target_id = find_nation_id(state, target_name)
                    if target_id and target_id != nation_id:
                        target = state.nations[target_id]
                        rel = nation.diplomacy.relations.get(target_id, 0)
                        if rel > 50 and target_id not in nation.diplomacy.alliances:
                            nation.diplomacy.alliances.append(target_id)
                            target.diplomacy.alliances.append(nation_id)
                            state.nations[target_id] = target
                            log_msg = f"★ {nation.name} and {target.name} have formed an alliance!"
                            logs.append(log_msg)
                            state.add_news(f"{nation.name} and {target.name} Sign Alliance Pact", nation_id, "diplomacy")
                            if broadcast_fn:
                                await broadcast_fn({"type": "turn_action", "message": log_msg, "action_type": "diplomacy"})

                elif action_type == "declare_war" and target_name:
                    target_id = find_nation_id(state, target_name)
                    aggression_mod = IDEOLOGY_AGGRESSION.get(nation.ideology, 0)
                    threshold = 0.6 - aggression_mod
                    if (target_id and target_id != nation_id and
                            nation.personality.aggression > threshold and
                            target_id != state.player_nation_id and
                            not nation.is_at_war and state.world_tension > 0.35):
                        target = state.nations[target_id]
                        if not target.is_at_war:
                            war = War(
                                attacker=nation_id,
                                defender=target_id,
                                start_turn=state.turn,
                                casus_belli="territorial_dispute"
                            )
                            state.active_wars.append(war)
                            nation.is_at_war = True
                            target.is_at_war = True
                            state.nations[target_id] = target
                            state.world_tension = min(1.0, state.world_tension + 0.05)
                            log_msg = f"⚔ {nation.name} has declared war on {target.name}!"
                            logs.append(log_msg)
                            state.add_news(f"WAR: {nation.name} Invades {target.name}", nation_id, "war")
                            if broadcast_fn:
                                await broadcast_fn({"type": "turn_action", "message": log_msg, "action_type": "war"})

                elif action_type == "boost_economy":
                    eco = nation.economy
                    eco.gdp_growth = min(0.1, eco.gdp_growth + 0.005)
                    nation.economy = eco
                    log_msg = f"{nation.name} implements economic stimulus"
                    logs.append(log_msg)
                    if broadcast_fn:
                        await broadcast_fn({"type": "turn_action", "message": log_msg, "action_type": "economy"})

                elif action_type == "build_army":
                    mil = nation.military
                    mil.army_size = int(mil.army_size * 1.02)
                    nation.military = mil
                    log_msg = f"{nation.name} expands its military forces"
                    logs.append(log_msg)
                    if broadcast_fn:
                        await broadcast_fn({"type": "turn_action", "message": log_msg, "action_type": "military"})

            state.nations[nation_id] = nation
        except Exception as e:
            logs.append(f"AI error for {nation.name}: {str(e)[:50]}")

    return state, logs


def process_war_reactions(state: GameState) -> tuple[GameState, list[str]]:
    """Third-party nations react to ongoing wars with sanctions, condemnations, or joining sides."""
    logs = []
    if not state.active_wars:
        return state, logs

    for war in state.active_wars:
        if war.status != "ongoing":
            continue
        attacker = state.nations.get(war.attacker)
        defender = state.nations.get(war.defender)
        if not attacker or not defender:
            continue

        for nation_id, nation in list(state.nations.items()):
            if nation_id in (war.attacker, war.defender) or not nation.is_alive or nation.is_at_war:
                continue
            if nation_id == state.player_nation_id:
                continue

            # Democratic nations condemn and sanction authoritarian aggressors
            if (nation.ideology in DEMOCRATIC_IDEOLOGIES and
                    attacker.ideology in AUTHORITARIAN_IDEOLOGIES and
                    war.attacker not in nation.diplomacy.sanctions_against and
                    random.random() < 0.12):
                nation.diplomacy.sanctions_against.append(war.attacker)
                attacker.economy.gdp_growth = max(-0.1, attacker.economy.gdp_growth - 0.005)
                state.nations[war.attacker] = attacker
                log = f"{nation.name} condemns {attacker.name}'s aggression and imposes sanctions"
                logs.append(log)
                state.add_news(f"{nation.name} Sanctions {attacker.name} Over War", nation_id, "diplomacy")

            # Ideologically aligned high-aggression nations might join wars
            elif (nation.personality.aggression > 0.72 and
                  state.world_tension > 0.5 and
                  nation.ideology == attacker.ideology and
                  nation_id not in war.attacker_allies and
                  nation_id not in war.defender_allies and
                  random.random() < 0.04):
                war.attacker_allies.append(nation_id)
                nation.is_at_war = True
                log = f"⚔ {nation.name} joins the war on {attacker.name}'s side!"
                logs.append(log)
                state.add_news(f"{nation.name} Enters War Alongside {attacker.name}", nation_id, "war")

            # Nations with defense pacts join the defender
            elif (nation_id in defender.diplomacy.defense_pacts and
                  nation_id not in war.defender_allies and
                  nation_id not in war.attacker_allies and
                  random.random() < 0.6):
                war.defender_allies.append(nation_id)
                nation.is_at_war = True
                log = f"⚔ {nation.name} honors its defense pact and joins {defender.name}!"
                logs.append(log)
                state.add_news(f"{nation.name} Enters War to Defend {defender.name}", nation_id, "war")

            state.nations[nation_id] = nation

    return state, logs


def build_game_summary(state: GameState) -> dict:
    nations_summary = {}
    for nid, n in state.nations.items():
        nations_summary[nid] = {
            "name": n.name,
            "ideology": n.ideology,
            "leader": n.leader,
            "stability": round(n.stability, 2),
            "war_support": round(n.war_support, 2),
            "is_at_war": n.is_at_war,
            "economy": {
                "gdp": round(n.economy.gdp, 1),
                "gdp_growth": round(n.economy.gdp_growth, 3),
                "unemployment": round(n.economy.unemployment, 2),
            },
            "military": {
                "army_size": n.military.army_size,
                "equipment_level": round(n.military.equipment_level, 2),
                "morale": round(n.military.morale, 2),
            },
            "diplomacy": {
                "alliances": n.diplomacy.alliances,
                "relations": {k: v for k, v in list(n.diplomacy.relations.items())[:10]},
            },
            "personality": {
                "aggression": n.personality.aggression,
                "diplomatic_tendency": n.personality.diplomatic_tendency,
                "historical_grievances": n.personality.historical_grievances[:3],
                "core_claims": n.personality.core_claims[:3],
            }
        }

    return {
        "turn": state.turn,
        "year": state.year,
        "month": state.month,
        "player_nation": state.player_nation_id,
        "world_tension": state.world_tension,
        "nations": nations_summary,
        "active_wars": [{"attacker": w.attacker, "defender": w.defender, "warscore": w.attacker_warscore} for w in state.active_wars],
    }


def find_nation_id(state: GameState, name: str) -> str | None:
    for nid, n in state.nations.items():
        if n.name.lower() == name.lower() or nid.lower() == name.lower():
            return nid
    return None


def _process_resource_trades(state: GameState) -> GameState:
    """Execute one turn of all active resource trades."""
    still_active = []
    for trade in state.resource_trades:
        if not trade.active or trade.turns_remaining <= 0:
            continue
        giver = state.nations.get(trade.initiator_id)
        receiver = state.nations.get(trade.target_id)
        if not giver or not receiver:
            continue

        # NPCs may suspend trade when player policies are hostile to them
        player = state.get_player_nation()
        if player and (trade.initiator_id == player.id or trade.target_id == player.id):
            npc_id = trade.target_id if trade.initiator_id == player.id else trade.initiator_id
            npc = state.nations.get(npc_id)
            if npc:
                from backend import npc_rules
                if npc_rules.policy_trade_blocked(npc.model_dump(), player.model_dump()):
                    trade.active = False
                    state.add_news(
                        f"{npc.name} suspends trade with {player.name} over policy differences",
                        npc.id,
                        "diplomacy",
                    )
                    continue

        # Transfer resources via stockpile (treat raw resources as stockpile entry)
        offer = trade.offer_resource
        request = trade.request_resource

        giver_stock = giver.economy.stockpile.get(offer, 0)
        if giver_stock >= trade.offer_amount:
            giver.economy.stockpile[offer] = giver_stock - trade.offer_amount
            receiver.economy.stockpile[offer] = receiver.economy.stockpile.get(offer, 0) + trade.offer_amount

        recv_stock = receiver.economy.stockpile.get(request, 0)
        if recv_stock >= trade.request_amount:
            receiver.economy.stockpile[request] = recv_stock - trade.request_amount
            giver.economy.stockpile[request] = giver.economy.stockpile.get(request, 0) + trade.request_amount

        state.nations[trade.initiator_id] = giver
        state.nations[trade.target_id] = receiver
        trade.turns_remaining -= 1
        still_active.append(trade)
    state.resource_trades = still_active
    return state


def _apply_policy_reactions(state: GameState) -> tuple[GameState, list[str]]:
    logs = []
    player = state.get_player_nation()
    if not player or not player.active_policies:
        return state, logs

    from backend import npc_rules

    for nid, npc in list(state.nations.items()):
        if nid == state.player_nation_id or not npc.is_alive:
            continue
        hostility = npc_rules.policy_hostility_score(npc.model_dump(), player.model_dump(), state.world_tension)
        if hostility < 1.5:
            continue

        # Base relation penalty scales with hostility
        rel_penalty = -2 if hostility < 3.0 else -5 if hostility < 4.5 else -8
        rel = npc.diplomacy.relations.get(state.player_nation_id, 0)
        npc.diplomacy.relations[state.player_nation_id] = max(-100, min(100, rel + rel_penalty))
        player_rel = player.diplomacy.relations.get(nid, 0)
        player.diplomacy.relations[nid] = max(-100, min(100, player_rel + int(rel_penalty * 0.6)))

        # Medium+ hostility: apply trade price pressure
        if hostility >= 3.0 and random.random() < 0.35:
            for trade in state.resource_trades:
                if not trade.active:
                    continue
                if trade.initiator_id == nid and trade.target_id == state.player_nation_id:
                    trade.offer_amount = max(1.0, trade.offer_amount * 0.9)
                    trade.request_amount = max(1.0, trade.request_amount * 1.1)
                elif trade.target_id == nid and trade.initiator_id == state.player_nation_id:
                    trade.offer_amount = max(1.0, trade.offer_amount * 0.9)
                    trade.request_amount = max(1.0, trade.request_amount * 1.1)

        # High hostility: consider sanctions
        if hostility >= 4.5 and state.world_tension > 0.35:
            if state.player_nation_id not in npc.diplomacy.sanctions_against and random.random() < 0.4:
                npc.diplomacy.sanctions_against.append(state.player_nation_id)
                logs.append(f"{npc.name} imposes sanctions on {player.name} over policy disputes")
                state.add_news(
                    f"{npc.name} Sanctions {player.name} Over Domestic Policy",
                    npc.id,
                    "diplomacy",
                )

        # High hostility: align with player rivals
        if hostility >= 4.5 and random.random() < 0.3:
            rival_id = None
            rival_score = 999
            for other_id, other in state.nations.items():
                if other_id in {nid, state.player_nation_id} or not other.is_alive:
                    continue
                rel_to_player = other.diplomacy.relations.get(state.player_nation_id, 0)
                if rel_to_player < rival_score:
                    rival_score = rel_to_player
                    rival_id = other_id
            if rival_id:
                rival = state.nations[rival_id]
                npc_rel = npc.diplomacy.relations.get(rival_id, 0)
                npc.diplomacy.relations[rival_id] = max(-100, min(100, npc_rel + 6))
                rival_rel = rival.diplomacy.relations.get(nid, 0)
                rival.diplomacy.relations[nid] = max(-100, min(100, rival_rel + 4))
                state.nations[rival_id] = rival
                logs.append(f"{npc.name} deepens ties with {rival.name} amid policy tensions")

        state.nations[nid] = npc

    state.nations[state.player_nation_id] = player
    return state, logs


async def process_full_turn(state: GameState, broadcast_fn=None) -> tuple[GameState, list[str]]:
    """Execute one complete game turn."""
    logs = []
    state.advance_date()
    header = f"--- Turn {state.turn}: {_month_name(state.month)} {state.year} ---"
    logs.append(header)
    if broadcast_fn:
        await broadcast_fn({"type": "turn_action", "message": header, "action_type": "header"})

    # 1. Economy, happiness, and research simulation
    for nid, nation in state.nations.items():
        if nation.is_alive:
            nation = simulate_economy(nation)
            nation = simulate_military_growth(nation)
            nation = apply_stability_effects(nation)
            nation = simulate_happiness(nation)
            nation = simulate_research(nation)
            nation = advance_research_projects(nation)
            if nid == state.player_nation_id:
                nation = apply_policy_effects(nation)
            nation = simulate_political_power(nation)
            state.nations[nid] = nation

    # 1b. Process active resource trades
    state = _process_resource_trades(state)

    # 2. Resolve ongoing wars
    still_active = []
    for war in state.active_wars:
        if war.status == "ongoing":
            war, war_logs = resolve_combat_turn(state, war)
            for wl in war_logs:
                logs.append(wl)
                if broadcast_fn:
                    await broadcast_fn({"type": "turn_action", "message": wl, "action_type": "war"})
            if war.status == "ongoing":
                still_active.append(war)
            else:
                att = state.nations.get(war.attacker)
                defen = state.nations.get(war.defender)
                if att:
                    att.is_at_war = False
                    state.nations[war.attacker] = att
                if defen:
                    defen.is_at_war = False
                    state.nations[war.defender] = defen
        else:
            still_active.append(war)
    state.active_wars = still_active

    # 3. World tension drift
    if state.active_wars:
        state.world_tension = min(1.0, state.world_tension + 0.005 * len(state.active_wars))
    else:
        state.world_tension = max(0.05, state.world_tension - 0.002)

    _inject_world_news(state)

    # 4. AI nations make decisions
    state, ai_logs = await process_ai_turns(state, broadcast_fn=broadcast_fn)
    logs.extend(ai_logs)

    # 5. Policy-based NPC reactions
    state, policy_logs = _apply_policy_reactions(state)
    for pl in policy_logs:
        logs.append(pl)
        if broadcast_fn:
            await broadcast_fn({"type": "turn_action", "message": pl, "action_type": "diplomacy"})

    # 6. Third-party war reactions
    state, reaction_logs = process_war_reactions(state)
    for rl in reaction_logs:
        logs.append(rl)
        if broadcast_fn:
            await broadcast_fn({"type": "turn_action", "message": rl, "action_type": "diplomacy"})

    # 7. Pull issues from the pre-written library — zero AI calls needed.
    player = state.get_player_nation()
    if player and len([i for i in state.pending_issues if not i.resolved]) < MAX_PENDING_ISSUES:
        from backend.issues_library import get_issues_for_context, format_issue_for_game, generate_auto_issue

        # Track which library issues have already been used this game
        used_ids = {i.source_id for i in state.pending_issues if i.source_id}

        issue_types = _pick_issue_types(player, state)
        want = MAX_PENDING_ISSUES - len([i for i in state.pending_issues if not i.resolved])

        # Build resolved-option map so chained issues can trigger
        resolved_options = {
            i.source_id: i.chosen_option
            for i in state.pending_issues
            if i.resolved and i.source_id and i.chosen_option is not None
        }

        game_context = {
            "stability": player.stability,
            "unemployment": player.economy.unemployment,
            "inflation": player.economy.inflation,
            "world_tension": state.world_tension,
            "happiness": player.happiness,
            "war_support": player.war_support,
            "gdp_growth": player.economy.gdp_growth,
            "prestige": player.prestige,
            "population": player.population,
            "resolved_options": resolved_options,
        }

        for itype in issue_types[:want * 2]:  # try a few types to fill slots
            if len([i for i in state.pending_issues if not i.resolved]) >= MAX_PENDING_ISSUES:
                break
            raw_issues = get_issues_for_context(
                year=state.year,
                ideology=player.ideology,
                issue_type=itype,
                at_war=player.is_at_war,
                used_ids=used_ids,
                count=1,
                game_context=game_context,
            )
            raw = raw_issues[0] if raw_issues else generate_auto_issue(
                issue_type=itype,
                ideology=player.ideology,
                game_context=game_context,
            )
            if not raw:
                continue
            issue_data = format_issue_for_game(raw)
            used_ids.add(raw["id"])

            options = [
                IssueOption(
                    id=o["id"], text=o["text"],
                    effects=o.get("effects", {}),
                    flavor=o.get("flavor", ""),
                    news=o.get("news", ""),
                )
                for o in issue_data.get("options", [])
            ]
            if not options:
                continue
            issue = Issue(
                title=issue_data["title"],
                description=issue_data["description"],
                issue_type=issue_data["issue_type"],
                urgency=issue_data["urgency"],
                options=options,
                advisors=issue_data.get("advisors", []),
                source_id=issue_data.get("source_id", ""),
            )
            state.pending_issues.append(issue)
            log_msg = f"New issue: {issue.title}"
            logs.append(log_msg)
            if broadcast_fn:
                await broadcast_fn({"type": "turn_action", "message": log_msg, "action_type": "politics"})

    state.turn_log = logs
    state.phase = "issues"
    return state, logs


def _pick_issue_types(player, state: GameState) -> list[str]:
    """Return issue types ordered by relevance to the current game situation."""
    types = []
    if player.is_at_war:
        types.append("military")
    if player.economy.gdp_growth < 0.01 or player.economy.unemployment > 0.15:
        types.append("economic")
    if player.stability < 0.5:
        types.append("political")
    if state.world_tension > 0.6 and "military" not in types:
        types.append("diplomatic")
    # Always have fallbacks
    for t in ["economic", "political", "social", "military", "diplomatic"]:
        if t not in types:
            types.append(t)
    return types



def _month_name(month: int) -> str:
    names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return names[month - 1] if 1 <= month <= 12 else str(month)


def _inject_world_news(state: GameState) -> None:
    headlines = [
        "Regional trade pact boosts industrial confidence",
        "Border talks resume amid rising tensions",
        "New infrastructure plan announced by major powers",
        "Energy prices stabilize after weeks of volatility",
        "Military exercises conclude without incident",
        "Diplomatic summit ends with cautious optimism",
    ]
    if random.random() < 0.5:
        headline = random.choice(headlines)
        state.add_news(headline, "world", "politics")


def _populate_state_from_world_data(
    state: GameState,
    world_data: dict,
    player_nation_name: str,
    ideology: str,
    world_tension_fallback: float,
) -> GameState:
    """Populate a GameState with nations from world_data (fallback or AI). Pure Python, no I/O."""
    from backend.models import EconomyStats, MilitaryStats, DiplomacyState, NationPersonality

    # Clear existing nations so this can be called a second time (AI upgrade)
    state.nations = {}
    state.player_nation_id = ""

    for nation_name, nation_data in world_data["nations"].items():
        nation_id = nation_name.lower().replace(" ", "_")
        player_name_norm = player_nation_name.lower().replace(" ", "_")
        is_player = (nation_name.lower() == player_nation_name.lower() or
                     nation_id == player_name_norm)

        eco_data = nation_data.get("economy", {})
        mil_data = nation_data.get("military", {})
        dip_data = nation_data.get("diplomacy", {})
        per_data = nation_data.get("personality", {})

        eco = EconomyStats(
            gdp=eco_data.get("gdp", 100),
            gdp_growth=eco_data.get("gdp_growth", 0.03),
            unemployment=eco_data.get("unemployment", 0.07),
            inflation=eco_data.get("inflation", 0.02),
            trade_balance=eco_data.get("trade_balance", 0),
            industry_output=eco_data.get("industry_output", 80),
            tax_rate=eco_data.get("tax_rate", 0.30),
            gov_spending=eco_data.get("gov_spending", 0.35),
            trade_openness=eco_data.get("trade_openness", 0.5),
            nationalization=eco_data.get("nationalization", 0.3),
        )
        mil = MilitaryStats(
            army_size=mil_data.get("army_size", 100000),
            navy_tonnage=mil_data.get("navy_tonnage", 50000),
            air_force=mil_data.get("air_force", 100),
            manpower_pool=mil_data.get("manpower_pool", 1000000),
            equipment_level=mil_data.get("equipment_level", 0.7),
            morale=mil_data.get("morale", 0.8),
            military_spending=mil_data.get("military_spending", 0.05),
        )
        dip = DiplomacyState(
            alliances=dip_data.get("alliances", []),
            defense_pacts=dip_data.get("defense_pacts", []),
            trade_deals=dip_data.get("trade_deals", []),
            sanctions_against=dip_data.get("sanctions_against", []),
            puppets=dip_data.get("puppets", []),
            relations={k.lower().replace(" ", "_"): v for k, v in dip_data.get("relations", {}).items()},
        )
        per = NationPersonality(
            aggression=per_data.get("aggression", 0.5),
            economic_priority=per_data.get("economic_priority", "balanced"),
            diplomatic_tendency=per_data.get("diplomatic_tendency", "neutral"),
            historical_grievances=per_data.get("historical_grievances", []),
            core_claims=per_data.get("core_claims", []),
        )
        if is_player:
            per.aggression = max(per.aggression, 0.1)

        color = IDEOLOGY_COLORS.get(nation_data.get("ideology", ""), nation_data.get("color", "#888888"))
        nation = Nation(
            id=nation_id,
            name=nation_name,
            capital=nation_data.get("capital", ""),
            leader=nation_data.get("leader", ""),
            ideology=nation_data.get("ideology", ideology if is_player else "Liberal Democracy"),
            government_type=nation_data.get("government_type", "Republic"),
            population=nation_data.get("population", 10_000_000),
            stability=nation_data.get("stability", 0.7),
            war_support=nation_data.get("war_support", 0.5),
            prestige=float(nation_data.get("prestige", 50)),
            is_player=is_player,
            color=color,
            economy=eco,
            military=mil,
            diplomacy=dip,
            personality=per,
        )
        state.nations[nation_id] = nation
        if is_player:
            state.player_nation_id = nation_id

    # Ensure player nation exists even if AI didn't generate it
    if not state.player_nation_id:
        from backend.models import EconomyStats, MilitaryStats, DiplomacyState, NationPersonality
        pid = player_nation_name.lower().replace(" ", "_")
        state.nations[pid] = Nation(
            id=pid, name=player_nation_name, ideology=ideology,
            is_player=True, color=IDEOLOGY_COLORS.get(ideology, "#3b82f6"),
            economy=EconomyStats(), military=MilitaryStats(),
            diplomacy=DiplomacyState(), personality=NationPersonality(),
        )
        state.player_nation_id = pid

    state.world_tension = world_data.get("world_tension", world_tension_fallback)

    # Apply era/country starting tech
    from backend.starting_tech import starting_nodes_for
    from backend.tech_nodes import get_node, apply_node_unlocks
    for nid, nation in state.nations.items():
        nodes = starting_nodes_for(state.era_id, nation.name)
        if not nodes:
            continue
        nation_data = nation.model_dump()
        researched = set(nation.tech_levels.get("researched_nodes", []))
        for node_id in nodes:
            node = get_node(node_id)
            if not node or node_id in researched:
                continue
            researched.add(node_id)
            nation_data = apply_node_unlocks(nation_data, node)
        nation_data.setdefault("tech_levels", {})["researched_nodes"] = list(researched)
        state.nations[nid] = Nation.model_validate(nation_data)
    return state


def initialize_game_instant(era_id: str, era_data: dict, player_nation_name: str, ideology: str) -> GameState:
    """
    Build a game state with the fallback world instantly — zero AI calls.
    Call this from the API endpoint so the response returns in <1 second.
    AI world gen should run as a background task via `run_ai_world_gen()`.
    """
    state = GameState(
        era_id=era_id,
        year=era_data["year"],
        world_tension=era_data.get("world_tension_base", 0.3),
    )
    major_nations = era_data.get("major_nations", [])
    world_data = _build_fallback_world(player_nation_name, ideology, major_nations)
    return _populate_state_from_world_data(
        state, world_data, player_nation_name, ideology,
        era_data.get("world_tension_base", 0.3),
    )


async def run_ai_world_gen(
    state: GameState, era_id: str, era_data: dict,
    player_nation_name: str, ideology: str,
) -> GameState:
    """
    Run the AI world generation and upgrade the state in-place.
    Called as a background task after the game response has already been sent.
    Returns the updated state so the caller can save + broadcast.
    """
    major_nations = era_data.get("major_nations", [])
    world_data = await ai_engine.generate_world_state(
        era_id, era_data["name"], player_nation_name, ideology, major_nations
    )
    if not world_data or "nations" not in world_data:
        print("AI world gen returned nothing — keeping fallback world")
        return state
    return _populate_state_from_world_data(
        state, world_data, player_nation_name, ideology,
        era_data.get("world_tension_base", 0.3),
    )


async def _seed_starter_content(era_name: str, ideology: str, year: int, state: GameState) -> None:
    """Background: pre-fill issue pool and starter news so turns 1-3 are instant."""
    from backend import database as db

    # Seed fallback issues first (instant, no AI)
    await db.seed_pool_if_empty(ai_engine._FALLBACK_ISSUES)

    # Generate AI issues for each type in parallel
    try:
        new_issues = await ai_engine.generate_starter_issues(era_name, ideology, year)
        for issue_data in new_issues:
            await db.add_pool_issue(issue_data)
        print(f"Starter pool seeded: {len(new_issues)} AI issues added")
    except Exception as e:
        print(f"Starter issue gen failed: {e}")

    # Generate opening news headlines and inject into the game state news feed
    try:
        from backend.models import NewsHeadline
        headlines = await ai_engine.generate_starter_news(era_name, "", year)
        for headline in headlines:
            state.news_feed.append(NewsHeadline(turn=0, headline=headline, nation="world", category="politics"))
    except Exception as e:
        print(f"Starter news gen failed: {e}")


def _build_fallback_world(player_nation: str, ideology: str, major_nations: list[str]) -> dict:
    nations = {}
    ideologies = ["Liberal Democracy", "Communism", "Fascism", "Monarchy", "Social Democracy", "Theocracy"]
    for i, name in enumerate(major_nations):
        is_player = name.lower() == player_nation.lower()
        nat_ideology = ideology if is_player else ideologies[i % len(ideologies)]
        nations[name] = {
            "name": name,
            "capital": f"{name} City",
            "leader": f"Leader of {name}",
            "ideology": nat_ideology,
            "government_type": "Republic",
            "population": random.randint(5_000_000, 100_000_000),
            "stability": round(random.uniform(0.5, 0.85), 2),
            "war_support": round(random.uniform(0.3, 0.7), 2),
            "prestige": random.randint(20, 80),
            "color": IDEOLOGY_COLORS.get(nat_ideology, "#888888"),
            "economy": {"gdp": random.randint(30, 500), "gdp_growth": 0.03, "unemployment": 0.08},
            "military": {"army_size": random.randint(50000, 500000), "equipment_level": 0.7, "morale": 0.75},
            "diplomacy": {"alliances": [], "relations": {}},
            "personality": {"aggression": round(random.uniform(0.2, 0.8), 2), "diplomatic_tendency": "neutral", "historical_grievances": [], "core_claims": []}
        }
    return {"nations": nations, "world_tension": 0.3}
