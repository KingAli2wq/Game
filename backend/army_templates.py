"""
Division templates for the HOI4-style army system.
Each template defines a division type with combat stats, costs, and training time.
"""

TEMPLATES: dict[str, dict] = {
    "infantry": {
        "id": "infantry",
        "name": "Infantry Division",
        "description": "Standard foot soldiers. Cheap, reliable, good at holding ground.",
        "icon": "INF",
        "color": "#4b7a3b",
        "attack": 15,
        "defense": 25,
        "breakthrough": 10,
        "speed": 1.0,
        "manpower_per_div": 10000,
        "equipment_cost": 500,
        "training_turns": 3,
        "upkeep_manpower": 50,   # per division per turn
    },
    "motorized": {
        "id": "motorized",
        "name": "Motorized Infantry",
        "description": "Fast-moving infantry in trucks. Excellent for exploiting breakthroughs.",
        "icon": "MOT",
        "color": "#c9a84c",
        "attack": 20,
        "defense": 20,
        "breakthrough": 18,
        "speed": 2.5,
        "manpower_per_div": 12000,
        "equipment_cost": 1200,
        "training_turns": 4,
        "upkeep_manpower": 60,
    },
    "armor": {
        "id": "armor",
        "name": "Armored Division",
        "description": "Tanks and mechanized support. Devastating breakthrough capability.",
        "icon": "ARM",
        "color": "#b06a2c",
        "attack": 40,
        "defense": 20,
        "breakthrough": 65,
        "speed": 3.0,
        "manpower_per_div": 8000,
        "equipment_cost": 3500,
        "training_turns": 6,
        "upkeep_manpower": 40,
    },
    "artillery": {
        "id": "artillery",
        "name": "Artillery Brigade",
        "description": "Heavy guns that devastate fortified positions and enemy formations.",
        "icon": "ART",
        "color": "#7a3030",
        "attack": 30,
        "defense": 10,
        "breakthrough": 5,
        "speed": 0.8,
        "manpower_per_div": 6000,
        "equipment_cost": 2500,
        "training_turns": 5,
        "upkeep_manpower": 30,
    },
    "special": {
        "id": "special",
        "name": "Special Forces",
        "description": "Elite troops for difficult terrain and critical objectives.",
        "icon": "SF",
        "color": "#4a2080",
        "attack": 35,
        "defense": 30,
        "breakthrough": 22,
        "speed": 1.8,
        "manpower_per_div": 5000,
        "equipment_cost": 5000,
        "training_turns": 8,
        "upkeep_manpower": 25,
    },
}

CONSCRIPTION_LAWS: dict[str, dict] = {
    "volunteer_only": {
        "id": "volunteer_only",
        "name": "Volunteer Only",
        "description": "Only volunteers serve. Minimal manpower drain on the economy.",
        "manpower_rate": 0.015,
        "stability_bonus": 0.01,
        "war_support_penalty": 0.0,
        "political_power_cost": 0,
    },
    "limited_conscription": {
        "id": "limited_conscription",
        "name": "Limited Conscription",
        "description": "A small mandatory service. Balances manpower and civilian morale.",
        "manpower_rate": 0.025,
        "stability_bonus": 0.0,
        "war_support_penalty": 0.0,
        "political_power_cost": 25,
    },
    "extensive_conscription": {
        "id": "extensive_conscription",
        "name": "Extensive Conscription",
        "description": "All eligible citizens serve. Economy takes a hit but armies are large.",
        "manpower_rate": 0.05,
        "stability_bonus": -0.01,
        "war_support_penalty": 0.0,
        "political_power_cost": 50,
    },
    "service_and_supply": {
        "id": "service_and_supply",
        "name": "Service and Supply",
        "description": "War economy. Maximum mobilization at significant stability cost.",
        "manpower_rate": 0.10,
        "stability_bonus": -0.02,
        "war_support_penalty": 0.0,
        "political_power_cost": 100,
    },
    "all_adults_serve": {
        "id": "all_adults_serve",
        "name": "All Adults Serve",
        "description": "Total war mobilization. Every adult is a soldier. Extreme stability penalty.",
        "manpower_rate": 0.20,
        "stability_bonus": -0.04,
        "war_support_penalty": 0.01,
        "political_power_cost": 200,
    },
}


def get_template(template_id: str) -> dict | None:
    return TEMPLATES.get(template_id)


def all_templates() -> list[dict]:
    return list(TEMPLATES.values())


def get_conscription_law(law_id: str) -> dict | None:
    return CONSCRIPTION_LAWS.get(law_id)


def all_conscription_laws() -> list[dict]:
    return list(CONSCRIPTION_LAWS.values())
