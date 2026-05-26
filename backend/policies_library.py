"""
Policy library — toggleable per-turn government decisions.
Players choose up to MAX_ACTIVE_POLICIES active at once.
"""
from typing import Optional

MAX_ACTIVE_POLICIES = 4

POLICIES = [
    # ─── Economic ─────────────────────────────────────────────────────────
    {
        "id": "free_market",
        "name": "Free Market",
        "icon": "📈",
        "category": "economic",
        "description": "Deregulate industry. Companies invest freely. Growth rises but inequality widens and stability dips.",
        "flavor": "The invisible hand, doing its thing.",
        "conflicts": ["state_industry", "welfare_state"],
        "ideology_favors": ["Liberal Democracy", "Conservative Democracy", "Oligarchy"],
        "effects": {
            "gdp_growth": 0.012,
            "happiness": -0.004,
            "stability": -0.004,
        },
    },
    {
        "id": "state_industry",
        "name": "State Industry",
        "icon": "🏭",
        "category": "economic",
        "description": "Government directs key industries. Employment rises. Market growth slows.",
        "flavor": "The five-year plan is ahead of schedule.",
        "conflicts": ["free_market"],
        "ideology_favors": ["Socialism", "Communism", "Social Democracy", "Technocracy"],
        "effects": {
            "gdp_growth": -0.008,
            "stability": 0.008,
            "unemployment": -0.008,
        },
    },
    {
        "id": "welfare_state",
        "name": "Welfare State",
        "icon": "🏥",
        "category": "economic",
        "description": "Comprehensive social safety net. Citizens are happier and society is stable.",
        "flavor": "No one should fall through the cracks.",
        "conflicts": ["austerity"],
        "ideology_favors": ["Social Democracy", "Socialism", "Communism"],
        "effects": {
            "happiness": 0.015,
            "stability": 0.010,
            "gdp_growth": -0.010,
        },
    },
    {
        "id": "austerity",
        "name": "Austerity",
        "icon": "✂️",
        "category": "economic",
        "description": "Cut government spending. Painful now, more stable books in the long run.",
        "flavor": "We cannot spend what we do not have.",
        "conflicts": ["welfare_state", "state_industry"],
        "ideology_favors": ["Conservative Democracy", "Oligarchy"],
        "effects": {
            "happiness": -0.015,
            "stability": -0.010,
            "gdp_growth": 0.008,
            "inflation": -0.010,
        },
    },
    # ─── Military ─────────────────────────────────────────────────────────
    {
        "id": "conscription",
        "name": "Conscription",
        "icon": "⚔️",
        "category": "military",
        "description": "Every citizen serves. Army grows each turn, but happiness falls.",
        "flavor": "Every able body, in service to the nation.",
        "conflicts": ["professional_army"],
        "ideology_favors": ["Fascism", "Communism", "Monarchy"],
        "effects": {
            "war_support": 0.006,
            "happiness": -0.010,
        },
    },
    {
        "id": "professional_army",
        "name": "Professional Army",
        "icon": "🎖️",
        "category": "military",
        "description": "Smaller but elite force. Higher morale, better equipment, more public trust.",
        "flavor": "Quality, not quantity.",
        "conflicts": ["conscription"],
        "ideology_favors": ["Liberal Democracy", "Conservative Democracy", "Technocracy"],
        "effects": {
            "war_support": 0.003,
            "happiness": 0.005,
            "stability": 0.005,
        },
    },
    {
        "id": "war_economy",
        "name": "War Economy",
        "icon": "🔧",
        "category": "military",
        "description": "Redirect the economy toward the war effort. Only viable during wartime.",
        "flavor": "Peace will come. First, victory.",
        "conflicts": ["free_market", "welfare_state"],
        "requires_at_war": True,
        "ideology_favors": [],
        "effects": {
            "war_support": 0.015,
            "happiness": -0.012,
            "gdp_growth": -0.005,
        },
    },
    # ─── Social ───────────────────────────────────────────────────────────
    {
        "id": "press_freedom",
        "name": "Free Press",
        "icon": "📰",
        "category": "social",
        "description": "Independent media builds trust. Stability rises but war support is harder to maintain.",
        "flavor": "The fourth estate, uncaged.",
        "conflicts": ["censorship"],
        "ideology_favors": ["Liberal Democracy", "Social Democracy", "Conservative Democracy"],
        "effects": {
            "stability": 0.012,
            "prestige": 0.5,
            "war_support": -0.006,
        },
    },
    {
        "id": "censorship",
        "name": "State Censorship",
        "icon": "📵",
        "category": "social",
        "description": "Control the narrative. War support rises. Trust and prestige quietly fall.",
        "flavor": "There is only one acceptable version of events.",
        "conflicts": ["press_freedom"],
        "ideology_favors": ["Fascism", "Communism", "Theocracy"],
        "effects": {
            "stability": -0.008,
            "war_support": 0.012,
            "prestige": -0.5,
            "happiness": -0.008,
        },
    },
    {
        "id": "public_education",
        "name": "Public Education",
        "icon": "📚",
        "category": "social",
        "description": "Invest in schools and universities. Research accelerates every turn.",
        "flavor": "An educated population is an unstoppable one.",
        "conflicts": [],
        "ideology_favors": [],
        "effects": {
            "research_points": 2.0,
            "stability": 0.005,
            "gdp_growth": -0.005,
        },
    },
    # ─── Diplomatic ───────────────────────────────────────────────────────
    {
        "id": "foreign_aid",
        "name": "Foreign Aid",
        "icon": "🤝",
        "category": "diplomatic",
        "description": "Generous aid programme. Earns international goodwill and prestige every turn.",
        "flavor": "Soft power is still power.",
        "conflicts": ["isolationism"],
        "ideology_favors": ["Liberal Democracy", "Social Democracy"],
        "effects": {
            "prestige": 1.0,
            "gdp_growth": -0.006,
            "stability": 0.003,
        },
    },
    {
        "id": "isolationism",
        "name": "Isolationism",
        "icon": "🏰",
        "category": "diplomatic",
        "description": "Close your borders. Internal stability rises. Global influence falls.",
        "flavor": "Our problems. Our solutions.",
        "conflicts": ["foreign_aid"],
        "ideology_favors": ["Monarchy", "Theocracy"],
        "effects": {
            "stability": 0.012,
            "gdp_growth": -0.010,
            "prestige": -0.5,
        },
    },
]


_EXTRA_POLICY_IDS = [
    "one_party_state",
    "forced_collectivization",
    "secret_police",
    "state_media",
    "election_ban",
    "military_dictatorship",
    "planned_economy",
    "nationalization",
    "press_restrictions",
    "surveillance_state",
    "political_purges",
    "privatization",
    "corporate_tax_cuts",
    "oligarchs",
    "foreign_corporations",
    "private_healthcare",
    "multi_party_elections",
    "extreme_privatisation",
    "worker_rights_ban",
    "corporate_monopolies",
    "union_busting",
    "open_borders",
    "multiculturalism",
    "pacifism",
    "civil_rights_expansion",
    "globalism",
    "free_press",
    "revolutionary_movements",
    "communism",
    "republicanism",
    "anti_religious_laws",
    "civilian_control",
    "mass_protests",
    "worker_unions",
    "atheism",
    "secularism",
    "lgbt_rights",
    "religious_freedom",
    "westernization",
    "immigration",
    "foreign_influence",
    "global_trade",
    "minority_autonomy",
    "high_taxes",
    "gun_bans",
    "heavy_regulation",
    "civil_liberties",
    "foreign_media",
    "high_corporate_tax",
    "worker_takeovers",
    "foreign_ownership",
    "western_influence",
    "privatized_healthcare",
    "foreign_bases",
    "military_blocs",
    "superpower_interference",
    "independent_judiciary",
    "worker_revolution",
    "union_power",
    "military_budget_cuts",
    "demilitarization",
    "western_alignment",
    "nato_membership",
    "soviet_alignment",
    "capitalism",
    "western_culture",
    "private_industry",
    "religious_influence",
    "minority_rights",
    "western_trade",
    "democracy",
    "internet_access",
]


def _titleize(policy_id: str) -> str:
    return policy_id.replace("_", " ").title()


_existing_ids = {p["id"] for p in POLICIES}
for _pid in _EXTRA_POLICY_IDS:
    if _pid in _existing_ids:
        continue
    POLICIES.append({
        "id": _pid,
        "name": _titleize(_pid),
        "icon": "⚑",
        "category": "ideological",
        "description": f"Adopt the {_titleize(_pid).lower()} stance.",
        "flavor": "This stance signals a clear direction for the nation.",
        "conflicts": [],
        "ideology_favors": [],
        "effects": {},
    })


def get_all_policies() -> list[dict]:
    return POLICIES


def get_policy(policy_id: str) -> Optional[dict]:
    return next((p for p in POLICIES if p["id"] == policy_id), None)


def get_policies_status(
    ideology: str,
    active_policies: list[str],
    is_at_war: bool = False,
    political_power: float | None = None,
) -> list[dict]:
    """Return all policies with their active/available/conflict status."""
    active_set = set(active_policies)
    result = []
    for p in POLICIES:
        requires_war = p.get("requires_at_war", False)
        available = not requires_war or is_at_war
        unavailable_reason = "Only available during wartime" if requires_war and not is_at_war else ""
        active_conflicts = [c for c in p.get("conflicts", []) if c in active_set]

        cost = get_policy_cost(p)
        can_afford = True if political_power is None else political_power >= cost
        result.append({
            **p,
            "active": p["id"] in active_set,
            "available": available,
            "unavailable_reason": unavailable_reason,
            "has_conflict": bool(active_conflicts),
            "conflict_ids": active_conflicts,
            "ideology_match": ideology in p.get("ideology_favors", []),
            "cost": cost,
            "can_afford": can_afford,
        })
    return result


def get_policy_cost(policy: dict) -> int:
    if "cost" in policy:
        return int(policy["cost"])
    effects = policy.get("effects", {})
    impact = 0.0
    for val in effects.values():
        if isinstance(val, (int, float)):
            impact += abs(float(val))
    base = 3.0
    cost = base + impact * 80.0
    return int(max(2, min(20, round(cost))))
