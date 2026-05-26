"""Hardcoded starting tech by era and country."""

BASE_BY_ERA = {
    "1815": ["inf_basic", "ind_basic", "dip_network", "eco_banking"],
    "1871": ["inf_basic", "ind_basic", "dip_network", "eco_banking", "res_labs"],
    "1914": ["inf_basic", "ind_basic", "dip_network", "eco_banking", "res_labs", "arm_light", "nav_basic"],
    "1936": ["inf_basic", "ind_basic", "dip_network", "eco_banking", "res_labs", "arm_light", "nav_basic", "air_basic"],
    "1945": ["inf_basic", "ind_basic", "dip_network", "eco_banking", "res_labs", "arm_light", "nav_basic", "air_basic", "air_fighters", "nav_destroyers", "ind_mass"],
    "1962": ["inf_basic", "ind_basic", "dip_network", "eco_banking", "res_labs", "arm_light", "nav_basic", "air_basic", "air_fighters", "nav_destroyers", "ind_mass", "dip_trade", "eco_welfare"],
    "1991": ["inf_basic", "ind_basic", "dip_network", "eco_banking", "res_labs", "arm_light", "nav_basic", "air_basic", "air_fighters", "nav_destroyers", "ind_mass", "dip_trade", "eco_welfare", "res_applied"],
    "2024": ["inf_basic", "ind_basic", "dip_network", "eco_banking", "res_labs", "arm_light", "nav_basic", "air_basic", "air_fighters", "nav_destroyers", "ind_mass", "dip_trade", "eco_welfare", "res_applied", "res_atomic", "dip_intel", "eco_keynesian"],
    "2050": ["inf_basic", "ind_basic", "dip_network", "eco_banking", "res_labs", "arm_light", "nav_basic", "air_basic", "air_fighters", "nav_destroyers", "ind_mass", "dip_trade", "eco_welfare", "res_applied", "res_atomic", "dip_intel", "eco_keynesian", "res_computing"],
}

COUNTRY_BONUSES = {
    "1936": {
        "Germany": ["arm_medium", "inf_tactics"],
        "United Kingdom": ["nav_destroyers", "air_fighters"],
        "United States": ["air_fighters", "res_applied"],
        "Soviet Union": ["inf_tactics", "ind_mass"],
        "Japan": ["nav_destroyers", "air_fighters"],
        "France": ["inf_tactics"],
    },
    "1945": {
        "United States": ["air_cas", "nav_capital"],
        "Soviet Union": ["arm_medium", "inf_tactics"],
        "United Kingdom": ["nav_capital"],
        "Germany": ["arm_medium"],
        "Japan": ["nav_destroyers"],
    },
    "1962": {
        "United States": ["air_cas", "nav_capital", "res_atomic"],
        "Soviet Union": ["arm_medium", "res_atomic"],
        "China": ["inf_tactics"],
    },
    "1991": {
        "United States": ["air_cas", "nav_capital", "res_computing"],
        "Russia": ["arm_medium"],
        "China": ["inf_tactics", "ind_mass"],
    },
    "2024": {
        "United States": ["air_cas", "nav_capital", "res_computing", "eco_globalisation"],
        "China": ["air_cas", "ind_war_eco"],
        "Russia": ["arm_medium", "nav_capital"],
        "United Kingdom": ["nav_capital"],
        "France": ["nav_capital"],
        "Germany": ["ind_war_eco"],
        "Japan": ["air_cas"],
        "India": ["ind_mass"],
    },
    "2050": {
        "United States": ["air_cas", "nav_capital", "res_computing", "eco_globalisation"],
        "China": ["air_cas", "ind_war_eco"],
        "India": ["ind_mass", "eco_globalisation"],
    },
}


def starting_nodes_for(era_id: str, country_name: str) -> list[str]:
    base = list(BASE_BY_ERA.get(era_id, BASE_BY_ERA.get("1936", [])))
    bonuses = COUNTRY_BONUSES.get(era_id, {}).get(country_name, [])
    return list(dict.fromkeys(base + bonuses))
