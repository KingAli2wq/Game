"""Rule-based NPC diplomacy logic (no AI required)."""

from __future__ import annotations

IDEOLOGY_DISLIKES = {
    "democracy": [
        "censorship",
        "one_party_state",
        "forced_collectivization",
        "secret_police",
        "state_media",
        "election_ban",
        "military_dictatorship",
    ],
    "liberal_democracy": [
        "state_industry",
        "planned_economy",
        "nationalization",
        "press_restrictions",
        "surveillance_state",
        "political_purges",
    ],
    "communism": [
        "free_market",
        "privatization",
        "corporate_tax_cuts",
        "oligarchs",
        "foreign_corporations",
        "private_healthcare",
        "press_freedom",
        "multi_party_elections",
    ],
    "socialism": [
        "extreme_privatisation",
        "worker_rights_ban",
        "austerity",
        "corporate_monopolies",
        "union_busting",
    ],
    "fascism": [
        "open_borders",
        "multiculturalism",
        "pacifism",
        "civil_rights_expansion",
        "globalism",
        "free_press",
    ],
    "monarchy": [
        "revolutionary_movements",
        "communism",
        "republicanism",
        "anti_religious_laws",
    ],
    "military_junta": [
        "civilian_control",
        "pacifism",
        "press_freedom",
        "mass_protests",
        "worker_unions",
    ],
    "theocracy": [
        "atheism",
        "secularism",
        "lgbt_rights",
        "religious_freedom",
        "westernization",
    ],
    "ultranationalist": [
        "immigration",
        "foreign_influence",
        "global_trade",
        "minority_autonomy",
    ],
    "libertarian": [
        "high_taxes",
        "surveillance_state",
        "gun_bans",
        "state_industry",
        "heavy_regulation",
    ],
    "authoritarian": [
        "free_press",
        "mass_protests",
        "multi_party_elections",
        "civil_liberties",
        "foreign_media",
    ],
    "capitalism": [
        "nationalization",
        "planned_economy",
        "high_corporate_tax",
        "worker_takeovers",
    ],
    "state_capitalist": [
        "foreign_ownership",
        "free_press",
        "western_influence",
    ],
    "social_democracy": [
        "austerity",
        "union_busting",
        "privatized_healthcare",
    ],
    "non_aligned": [
        "foreign_bases",
        "military_blocs",
        "superpower_interference",
    ],
    "isolationist": [
        "global_trade",
        "foreign_media",
        "immigration",
    ],
    "totalitarian": [
        "civil_liberties",
        "multi_party_elections",
        "independent_judiciary",
    ],
    "corporatist": [
        "worker_revolution",
        "communism",
        "union_power",
    ],
    "militarist": [
        "pacifism",
        "military_budget_cuts",
        "demilitarization",
    ],
}


COUNTRY_IDEOLOGIES = {
    "usa": ["liberal_democracy", "capitalist"],
    "canada": ["liberal_democracy", "social_democracy"],
    "mexico": ["democracy", "mixed_economy"],
    "cuba": ["communism", "authoritarian"],
    "brazil": ["democracy", "capitalist"],
    "argentina": ["democracy", "mixed_economy"],
    "chile_1975": ["military_junta", "capitalist"],
    "venezuela": ["socialism", "authoritarian"],
    "colombia": ["democracy", "capitalist"],
    "uk": ["liberal_democracy", "capitalist"],
    "france": ["liberal_democracy", "social_democracy"],
    "west_germany": ["liberal_democracy", "capitalist"],
    "italy": ["democracy", "capitalist"],
    "spain_franco": ["fascism", "authoritarian"],
    "portugal_salazar": ["authoritarian", "corporatist"],
    "ussr": ["communism", "authoritarian"],
    "east_germany": ["communism", "authoritarian"],
    "poland_communist": ["communism", "authoritarian"],
    "romania_ceausescu": ["communism", "authoritarian"],
    "yugoslavia": ["socialism", "non_aligned"],
    "albania_hoxha": ["communism", "isolationist"],
    "sweden": ["social_democracy"],
    "norway": ["social_democracy"],
    "denmark": ["social_democracy"],
    "finland_coldwar": ["democracy", "neutral"],
    "saudi_arabia": ["monarchy", "theocracy"],
    "iran_1979": ["theocracy", "authoritarian"],
    "iraq_saddam": ["authoritarian", "nationalist"],
    "syria_baathist": ["authoritarian", "socialism"],
    "israel": ["liberal_democracy", "capitalist"],
    "turkey_1980": ["military_junta", "nationalist"],
    "south_africa_apartheid": ["authoritarian", "nationalist"],
    "egypt_nasser": ["socialism", "authoritarian"],
    "libya_gaddafi": ["socialism", "authoritarian"],
    "ethiopia_derg": ["communism", "military_junta"],
    "congo_zaire": ["dictatorship", "capitalist"],
    "china_mao": ["communism", "authoritarian"],
    "china_modern": ["authoritarian", "state_capitalist"],
    "japan": ["liberal_democracy", "capitalist"],
    "south_korea_1980": ["authoritarian", "capitalist"],
    "north_korea": ["communism", "totalitarian"],
    "vietnam": ["communism", "authoritarian"],
    "cambodia_khmerrouge": ["communism", "ultra_authoritarian"],
    "india": ["democracy", "mixed_economy"],
    "pakistan_1980": ["military_junta", "authoritarian"],
    "indonesia_suharto": ["authoritarian", "capitalist"],
    "australia": ["liberal_democracy", "capitalist"],
    "new_zealand": ["social_democracy"],
    "nazi_germany": ["fascism", "ultranationalist"],
    "fascist_italy": ["fascism", "authoritarian"],
    "imperial_japan": ["militarist", "ultranationalist"],
    "khmer_rouge": ["communism", "ultra_authoritarian"],
}



def _relation_score(rel: int) -> float:
    return max(-100, min(100, rel))


def _ideology_alignment(target_ideology: str, player_ideology: str) -> float:
    if not target_ideology or not player_ideology:
        return 0.0
    if target_ideology == player_ideology:
        return 15.0
    democratic = {"Liberal Democracy", "Social Democracy", "Conservative Democracy"}
    authoritarian = {"Fascism", "Communism", "Oligarchy", "Theocracy"}
    if target_ideology in democratic and player_ideology in democratic:
        return 8.0
    if target_ideology in authoritarian and player_ideology in authoritarian:
        return 6.0
    if target_ideology in democratic and player_ideology in authoritarian:
        return -12.0
    if target_ideology in authoritarian and player_ideology in democratic:
        return -12.0
    return -2.0


def _tension_factor(world_tension: float, action_type: str) -> float:
    if world_tension is None:
        return 0.0
    # Higher tension makes alliances and defense pacts more likely.
    if action_type in {"form_alliance", "defense_pact", "alliance_tier_2", "alliance_tier_3"}:
        return (world_tension - 0.4) * 25
    # High tension reduces appetite for trade/tech
    if action_type in {"trade_deal", "buy_technology", "joint_research"}:
        return (0.3 - world_tension) * 10
    return 0.0


def _govt_factor(player_ideology: str, action_type: str) -> float:
    if not player_ideology:
        return 0.0
    if action_type == "form_alliance" and player_ideology in {"Fascism", "Communism"}:
        return -8.0
    if action_type == "improve_relations" and player_ideology in {"Liberal Democracy", "Social Democracy"}:
        return 5.0
    return 0.0


def _normalize_key(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def _get_country_ideologies(target_nation: dict) -> list[str]:
    name_key = _normalize_key(target_nation.get("name", ""))
    mapped = COUNTRY_IDEOLOGIES.get(name_key)
    if mapped:
        return mapped
    ideology = target_nation.get("ideology", "")
    return [_normalize_key(ideology)] if ideology else []


def _policy_alignment_score(target_ideologies: list[str], player_policies: list[str]) -> float:
    if not target_ideologies or not player_policies:
        return 0.0
    from backend.policies_library import get_policy
    score = 0.0
    for policy_id in player_policies:
        policy = get_policy(policy_id)
        if not policy:
            continue
        favors = [_normalize_key(i) for i in policy.get("ideology_favors", [])]
        dislikes = []
        for ideology in target_ideologies:
            dislikes.extend(IDEOLOGY_DISLIKES.get(ideology, []))
        if policy_id in dislikes:
            score -= 6.0
            continue
        if not favors:
            continue
        if any(ideo in favors for ideo in target_ideologies):
            score += 3.0
        else:
            score -= 2.0
    return score


def policy_trade_blocked(target_nation: dict, player_nation: dict) -> bool:
    target_ideologies = _get_country_ideologies(target_nation)
    player_policies = player_nation.get("active_policies", [])
    policy_score = _policy_alignment_score(target_ideologies, player_policies)
    rel = target_nation.get("diplomacy", {}).get("relations", {}).get(player_nation.get("name", ""), 0)
    return policy_score <= -6.0 and rel < 20


def policy_hostility_score(target_nation: dict, player_nation: dict, world_tension: float) -> float:
    target_ideologies = _get_country_ideologies(target_nation)
    player_policies = player_nation.get("active_policies", [])
    policy_score = _policy_alignment_score(target_ideologies, player_policies)
    rel = target_nation.get("diplomacy", {}).get("relations", {}).get(player_nation.get("name", ""), 0)
    rel_factor = max(0.2, (40 - rel) / 40.0)
    tension_factor = 0.7 + max(0.0, min(1.0, world_tension))
    return max(0.0, (-policy_score) * rel_factor * tension_factor * 0.5)


def diplomatic_response(
    target_nation: dict,
    player_nation: dict,
    action_type: str,
    details: dict,
    world_tension: float = 0.0,
) -> dict:
    rel = target_nation.get("diplomacy", {}).get("relations", {}).get(player_nation.get("name", ""), 0)
    rel_score = _relation_score(rel)
    ideology_score = _ideology_alignment(target_nation.get("ideology", ""), player_nation.get("ideology", ""))
    tension_score = _tension_factor(world_tension, action_type)
    govt_score = _govt_factor(player_nation.get("ideology", ""), action_type)

    policy_score = _policy_alignment_score(
        _get_country_ideologies(target_nation),
        player_nation.get("active_policies", []),
    )
    base = rel_score * 0.6 + ideology_score + tension_score + govt_score + policy_score

    thresholds = {
        "improve_relations": -10,
        "trade_deal": 5,
        "defense_pact": 20,
        "form_alliance": 35,
        "impose_sanctions": 10,
        "lift_sanctions": -5,
        "alliance_tier_1": 10,
        "alliance_tier_2": 20,
        "alliance_tier_3": 35,
    }
    threshold = thresholds.get(action_type, 15)
    accepted = base >= threshold
    relation_change = 6 if accepted else -4

    counteroffer = None
    if not accepted and action_type == "form_alliance":
        counteroffer = "We might consider a defense pact first."
    elif not accepted and action_type == "defense_pact":
        counteroffer = "Perhaps a trade agreement would build trust."

    return {
        "accepted": accepted,
        "response_message": f"{target_nation.get('name')} {'accepts' if accepted else 'declines'} the proposal.",
        "relation_change": relation_change,
        "counteroffer": counteroffer,
    }


def resource_trade_response(target_nation: dict, player_nation: dict, offer_amount: float, request_amount: float) -> dict:
    rel = target_nation.get("diplomacy", {}).get("relations", {}).get(player_nation.get("name", ""), 0)
    generosity = (offer_amount + 1) / (request_amount + 1)
    policy_score = _policy_alignment_score(
        _get_country_ideologies(target_nation),
        player_nation.get("active_policies", []),
    )
    if policy_trade_blocked(target_nation, player_nation):
        return {
            "accepted": False,
            "response_message": f"{target_nation.get('name')} halts trade over policy disagreements.",
            "counteroffer": None,
        }
    score = rel * 0.5 + (generosity - 1) * 40 + policy_score * 1.5
    accepted = score > 10
    return {
        "accepted": accepted,
        "response_message": f"{target_nation.get('name')} {'agrees to' if accepted else 'declines'} the resource trade.",
        "counteroffer": None,
    }


def troop_request_response(target_nation: dict, player_nation: dict, troops_requested: int) -> dict:
    rel = target_nation.get("diplomacy", {}).get("relations", {}).get(player_nation.get("name", ""), 0)
    is_ally = player_nation.get("name", "") in str(target_nation.get("diplomacy", {}).get("alliances", []))
    accepted = is_ally or rel > 35
    troops_sent = min(troops_requested, target_nation.get("military", {}).get("army_size", 0) // 6) if accepted else 0
    return {
        "accepted": accepted,
        "troops_sent": troops_sent,
        "response_message": f"{target_nation.get('name')} {'sends reinforcements' if accepted else 'declines to commit troops'}.",
    }


def tech_purchase_response(target_nation: dict, player_nation: dict, price_gdp: float) -> dict:
    rel = target_nation.get("diplomacy", {}).get("relations", {}).get(player_nation.get("name", ""), 0)
    policy_score = _policy_alignment_score(
        _get_country_ideologies(target_nation),
        player_nation.get("active_policies", []),
    )
    accepted = rel + policy_score > 30 and price_gdp >= 20
    return {
        "accepted": accepted,
        "response_message": f"{target_nation.get('name')} {'agrees to transfer' if accepted else 'refuses to share'} technology.",
    }


def joint_research_response(target_nation: dict, player_nation: dict) -> dict:
    rel = target_nation.get("diplomacy", {}).get("relations", {}).get(player_nation.get("name", ""), 0)
    policy_score = _policy_alignment_score(
        _get_country_ideologies(target_nation),
        player_nation.get("active_policies", []),
    )
    accepted = rel + policy_score > 15
    return {
        "accepted": accepted,
        "response_message": f"{target_nation.get('name')} {'joins' if accepted else 'declines'} the joint research program.",
    }
