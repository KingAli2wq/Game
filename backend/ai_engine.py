"""
Smart rule-based NPC engine — no AI server required.
Drop-in replacement for the old LLM-backed ai_engine.py.
All public function signatures are identical so game_logic.py and main.py need no changes.
"""

from __future__ import annotations
import random
import os
import asyncio
from typing import AsyncGenerator

AI_BASE_URL = "http://10.0.0.80:1234/v1"
AI_ENABLED = False   # permanently off — rule engine handles everything
MODEL_ID = "npc-engine-v2"


# ── Compatibility stubs ───────────────────────────────────────────────────────

async def get_model_id() -> str:
    return MODEL_ID


async def check_ai_server() -> dict:
    return {"status": "offline", "error": "Using built-in NPC engine (no AI server needed)", "url": AI_BASE_URL}


def _extract_json(text: str):
    return None


async def stream_ai(messages, temperature=0.7, max_tokens=200) -> AsyncGenerator[str, None]:
    yield "[NPC engine active — no AI server needed]"


# ── Historical World Data ─────────────────────────────────────────────────────
# Format: nation_name -> (capital, leader, ideology, gdp_billions, army_thousands, aggression_0_to_1)

_ERA_NATION_DATA: dict[str, dict[str, tuple]] = {
    "1936": {
        "Germany":              ("Berlin",          "Adolf Hitler",              "Fascism",                382,  500, 0.88),
        "France":               ("Paris",            "Léon Blum",                "Social Democracy",       206,  400, 0.42),
        "United Kingdom":       ("London",           "Neville Chamberlain",      "Conservative Democracy", 284,  200, 0.40),
        "Italy":                ("Rome",             "Benito Mussolini",         "Fascism",                141,  300, 0.75),
        "Soviet Union":         ("Moscow",           "Joseph Stalin",            "Communism",              310, 1500, 0.72),
        "United States":        ("Washington D.C.",  "Franklin D. Roosevelt",    "Liberal Democracy",     1057,  174, 0.28),
        "Japan":                ("Tokyo",            "Hirohito",                 "Fascism",                169,  300, 0.80),
        "Spain":                ("Madrid",           "Francisco Franco",         "Fascism",                 40,  180, 0.65),
        "Poland":               ("Warsaw",           "Ignacy Mościcki",          "Conservative Democracy",  46,  280, 0.50),
        "Romania":              ("Bucharest",        "Carol II",                 "Monarchy",                14,  120, 0.50),
        "Yugoslavia":           ("Belgrade",         "Peter II",                 "Monarchy",                12,  150, 0.52),
        "Hungary":              ("Budapest",         "Miklós Horthy",            "Monarchy",                11,   80, 0.58),
        "Czechoslovakia":       ("Prague",           "Edvard Beneš",             "Liberal Democracy",       27,  350, 0.38),
        "Austria":              ("Vienna",           "Kurt Schuschnigg",         "Monarchy",                16,   50, 0.36),
        "Belgium":              ("Brussels",         "Leopold III",              "Liberal Democracy",       37,  100, 0.36),
        "Netherlands":          ("The Hague",        "Wilhelmina",               "Liberal Democracy",       37,   70, 0.35),
        "Sweden":               ("Stockholm",        "Gustav V",                 "Social Democracy",        30,   60, 0.28),
        "Norway":               ("Oslo",             "Johan Nygaardsvold",       "Social Democracy",        14,   50, 0.28),
        "Denmark":              ("Copenhagen",       "Christian X",              "Social Democracy",        11,   40, 0.28),
        "Finland":              ("Helsinki",         "Kyösti Kallio",            "Liberal Democracy",       12,  130, 0.45),
        "Switzerland":          ("Bern",             "Federal Council",          "Liberal Democracy",       23,   30, 0.18),
        "China":                ("Nanjing",          "Chiang Kai-shek",          "Conservative Democracy",  80, 2000, 0.52),
        "Turkey":               ("Ankara",           "Mustafa Kemal Atatürk",    "Liberal Democracy",       18,  200, 0.46),
        "Brazil":               ("Rio de Janeiro",   "Getúlio Vargas",           "Oligarchy",               32,  100, 0.44),
        "Mexico":               ("Mexico City",      "Lázaro Cárdenas",          "Socialism",               22,   70, 0.40),
        "Canada":               ("Ottawa",           "William Lyon Mackenzie King","Liberal Democracy",     120,   40, 0.28),
        "Australia":            ("Canberra",         "Joseph Lyons",             "Liberal Democracy",       65,   30, 0.30),
        "India":                ("New Delhi",        "Viceroy Linlithgow",       "Conservative Democracy",  70,  150, 0.38),
        "South Africa":         ("Pretoria",         "J.B.M. Hertzog",           "Conservative Democracy",  25,   80, 0.48),
        "Argentina":            ("Buenos Aires",     "Agustín Justo",            "Oligarchy",               52,   80, 0.42),
        "Ethiopia":             ("Addis Ababa",      "Haile Selassie",           "Monarchy",                 3,   80, 0.52),
        "Greece":               ("Athens",           "Ioannis Metaxas",          "Monarchy",                 8,  100, 0.52),
        "Portugal":             ("Lisbon",           "António Salazar",          "Fascism",                 10,   60, 0.50),
        "Iraq":                 ("Baghdad",          "Ghazi I",                  "Monarchy",                 4,   45, 0.55),
        "Iran":                 ("Tehran",           "Reza Shah Pahlavi",        "Monarchy",                 6,  120, 0.50),
        "Saudi Arabia":         ("Riyadh",           "Ibn Saud",                 "Monarchy",                 3,   40, 0.48),
    },
    "1950": {
        "United States":        ("Washington D.C.",  "Harry S. Truman",          "Liberal Democracy",     2200, 1500, 0.48),
        "Soviet Union":         ("Moscow",           "Joseph Stalin",            "Communism",              950, 4000, 0.68),
        "United Kingdom":       ("London",           "Clement Attlee",           "Social Democracy",       500,  800, 0.40),
        "France":               ("Paris",            "Vincent Auriol",           "Social Democracy",       310,  500, 0.40),
        "China":                ("Beijing",          "Mao Zedong",               "Communism",              180, 3000, 0.65),
        "West Germany":         ("Bonn",             "Konrad Adenauer",          "Conservative Democracy", 310,  200, 0.32),
        "East Germany":         ("East Berlin",      "Wilhelm Pieck",            "Communism",              110,  100, 0.52),
        "Japan":                ("Tokyo",            "Shigeru Yoshida",          "Liberal Democracy",      150,  100, 0.26),
        "South Korea":          ("Seoul",            "Syngman Rhee",             "Conservative Democracy",  12,  250, 0.58),
        "North Korea":          ("Pyongyang",        "Kim Il-sung",              "Communism",                8,  250, 0.80),
        "India":                ("New Delhi",        "Jawaharlal Nehru",         "Social Democracy",       180,  400, 0.40),
        "Pakistan":             ("Karachi",          "Liaquat Ali Khan",         "Conservative Democracy",  15,  150, 0.52),
        "Turkey":               ("Ankara",           "Adnan Menderes",           "Liberal Democracy",       22,  500, 0.46),
        "Yugoslavia":           ("Belgrade",         "Josip Broz Tito",          "Socialism",               18,  350, 0.55),
        "Poland":               ("Warsaw",           "Bolesław Bierut",          "Communism",               35,  280, 0.50),
        "Czechoslovakia":       ("Prague",           "Klement Gottwald",         "Communism",               30,  200, 0.48),
        "Hungary":              ("Budapest",         "Mátyás Rákosi",            "Communism",               20,  120, 0.50),
        "Romania":              ("Bucharest",        "Gheorghe Gheorghiu-Dej",   "Communism",               18,  200, 0.50),
        "Bulgaria":             ("Sofia",            "Valko Chervenkov",         "Communism",               10,  150, 0.50),
        "Albania":              ("Tirana",           "Enver Hoxha",              "Communism",                3,   70, 0.60),
        "Israel":               ("Jerusalem",        "David Ben-Gurion",         "Social Democracy",        15,  150, 0.62),
        "Egypt":                ("Cairo",            "Farouk I",                 "Monarchy",                22,  150, 0.52),
        "Iran":                 ("Tehran",           "Mohammad Mosaddegh",       "Liberal Democracy",       18,  180, 0.48),
        "Brazil":               ("Rio de Janeiro",   "Getúlio Vargas",           "Socialism",               50,  180, 0.44),
        "Argentina":            ("Buenos Aires",     "Juan Perón",               "Socialism",               55,  130, 0.50),
        "Mexico":               ("Mexico City",      "Miguel Alemán Valdés",     "Liberal Democracy",       45,  100, 0.40),
        "Canada":               ("Ottawa",           "Louis St. Laurent",        "Liberal Democracy",      240,  100, 0.28),
        "Australia":            ("Canberra",         "Robert Menzies",           "Liberal Democracy",      140,   80, 0.28),
        "Italy":                ("Rome",             "Alcide De Gasperi",        "Conservative Democracy", 200,  300, 0.36),
        "Spain":                ("Madrid",           "Francisco Franco",         "Fascism",                 60,  200, 0.60),
        "Sweden":               ("Stockholm",        "Tage Erlander",            "Social Democracy",        55,   60, 0.26),
        "Greece":               ("Athens",           "Alexandros Papagos",       "Conservative Democracy",  12,  150, 0.50),
    },
    "1980": {
        "United States":        ("Washington D.C.",  "Jimmy Carter",             "Liberal Democracy",     6800, 2200, 0.44),
        "Soviet Union":         ("Moscow",           "Leonid Brezhnev",          "Communism",             2200, 5000, 0.65),
        "China":                ("Beijing",          "Deng Xiaoping",            "Communism",              700, 4000, 0.52),
        "West Germany":         ("Bonn",             "Helmut Schmidt",           "Social Democracy",       900,  500, 0.32),
        "Japan":                ("Tokyo",            "Masayoshi Ohira",          "Liberal Democracy",     1400,  250, 0.26),
        "United Kingdom":       ("London",           "Margaret Thatcher",        "Conservative Democracy", 760,  350, 0.40),
        "France":               ("Paris",            "Valéry Giscard d'Estaing", "Conservative Democracy", 690,  500, 0.40),
        "Italy":                ("Rome",             "Francesco Cossiga",        "Conservative Democracy", 490,  380, 0.36),
        "India":                ("New Delhi",        "Indira Gandhi",            "Social Democracy",       420, 1200, 0.44),
        "Brazil":               ("Brasília",         "João Figueiredo",          "Oligarchy",              360,  400, 0.46),
        "Canada":               ("Ottawa",           "Pierre Trudeau",           "Liberal Democracy",      580,   90, 0.28),
        "Australia":            ("Canberra",         "Malcolm Fraser",           "Conservative Democracy", 280,   80, 0.28),
        "Iran":                 ("Tehran",           "Ayatollah Khomeini",       "Theocracy",              120,  400, 0.70),
        "Iraq":                 ("Baghdad",          "Saddam Hussein",           "Oligarchy",               90,  430, 0.75),
        "Saudi Arabia":         ("Riyadh",           "Khalid bin Abdulaziz",     "Monarchy",               130,  150, 0.50),
        "Turkey":               ("Ankara",           "Kenan Evren",              "Oligarchy",              130,  600, 0.52),
        "Yugoslavia":           ("Belgrade",         "Josip Broz Tito",          "Socialism",               90,  250, 0.48),
        "Poland":               ("Warsaw",           "Edward Gierek",            "Communism",              100,  300, 0.46),
        "East Germany":         ("East Berlin",      "Erich Honecker",           "Communism",              140,  200, 0.50),
        "Vietnam":              ("Hanoi",            "Lê Duẩn",                  "Communism",               22, 1200, 0.60),
        "North Korea":          ("Pyongyang",        "Kim Il-sung",              "Communism",               20,  700, 0.82),
        "South Korea":          ("Seoul",            "Chun Doo-hwan",            "Oligarchy",              120,  650, 0.52),
        "Mexico":               ("Mexico City",      "José López Portillo",      "Liberal Democracy",      270,  120, 0.40),
        "Argentina":            ("Buenos Aires",     "Jorge Rafael Videla",      "Oligarchy",              140,  200, 0.58),
        "Pakistan":             ("Islamabad",        "Muhammad Zia-ul-Haq",      "Oligarchy",               60,  450, 0.58),
        "Egypt":                ("Cairo",            "Anwar Sadat",              "Oligarchy",               75,  450, 0.52),
        "Nigeria":              ("Lagos",            "Olusegun Obasanjo",        "Oligarchy",               90,  200, 0.50),
        "South Africa":         ("Pretoria",         "P.W. Botha",               "Oligarchy",              140,  300, 0.56),
        "Israel":               ("Jerusalem",        "Menachem Begin",           "Liberal Democracy",       85,  500, 0.62),
        "Cuba":                 ("Havana",           "Fidel Castro",             "Communism",               18,  250, 0.62),
        "Sweden":               ("Stockholm",        "Thorbjörn Fälldin",        "Social Democracy",       210,   70, 0.26),
        "Spain":                ("Madrid",           "Adolfo Suárez",            "Liberal Democracy",      300,  250, 0.38),
        "Libya":                ("Tripoli",          "Muammar Gaddafi",          "Socialism",               35,   60, 0.68),
        "Syria":                ("Damascus",         "Hafez al-Assad",           "Socialism",               22,  200, 0.65),
        "Indonesia":            ("Jakarta",          "Suharto",                  "Oligarchy",              160,  280, 0.50),
    },
    "2000": {
        "United States":        ("Washington D.C.",  "Bill Clinton",             "Liberal Democracy",    10500, 1400, 0.40),
        "China":                ("Beijing",          "Jiang Zemin",              "Communism",             4000, 2500, 0.52),
        "Japan":                ("Tokyo",            "Yoshiro Mori",             "Liberal Democracy",     3600,  250, 0.24),
        "Germany":              ("Berlin",           "Gerhard Schröder",         "Social Democracy",      2200,  350, 0.28),
        "United Kingdom":       ("London",           "Tony Blair",               "Social Democracy",      1800,  250, 0.38),
        "France":               ("Paris",            "Jacques Chirac",           "Conservative Democracy",1650,  350, 0.38),
        "India":                ("New Delhi",        "Atal Bihari Vajpayee",     "Conservative Democracy",1800, 1200, 0.40),
        "Italy":                ("Rome",             "Giuliano Amato",           "Liberal Democracy",     1350,  270, 0.32),
        "Canada":               ("Ottawa",           "Jean Chrétien",            "Liberal Democracy",      900,   60, 0.26),
        "Brazil":               ("Brasília",         "Fernando Cardoso",         "Liberal Democracy",     1100,  280, 0.38),
        "Russia":               ("Moscow",           "Vladimir Putin",           "Oligarchy",             1350, 1000, 0.62),
        "South Korea":          ("Seoul",            "Kim Dae-jung",             "Liberal Democracy",      700,  700, 0.44),
        "Australia":            ("Canberra",         "John Howard",              "Conservative Democracy", 600,   70, 0.30),
        "Mexico":               ("Mexico City",      "Vicente Fox",              "Liberal Democracy",      700,  200, 0.36),
        "Indonesia":            ("Jakarta",          "Abdurrahman Wahid",        "Liberal Democracy",      540,  400, 0.40),
        "Turkey":               ("Ankara",           "Ahmet Necdet Sezer",       "Liberal Democracy",      500,  650, 0.46),
        "Iran":                 ("Tehran",           "Mohammad Khatami",         "Theocracy",              420,  520, 0.58),
        "Saudi Arabia":         ("Riyadh",           "Abdullah bin Abdulaziz",   "Monarchy",               400,  200, 0.50),
        "Pakistan":             ("Islamabad",        "Pervez Musharraf",         "Oligarchy",              280,  620, 0.58),
        "North Korea":          ("Pyongyang",        "Kim Jong-il",              "Communism",               35, 1000, 0.84),
        "Argentina":            ("Buenos Aires",     "Fernando de la Rúa",       "Liberal Democracy",      480,   80, 0.38),
        "South Africa":         ("Pretoria",         "Thabo Mbeki",              "Liberal Democracy",      400,   80, 0.36),
        "Nigeria":              ("Abuja",            "Olusegun Obasanjo",        "Liberal Democracy",      280,   80, 0.46),
        "Egypt":                ("Cairo",            "Hosni Mubarak",            "Oligarchy",              290,  450, 0.48),
        "Israel":               ("Jerusalem",        "Ehud Barak",               "Liberal Democracy",      220,  500, 0.62),
        "Iraq":                 ("Baghdad",          "Saddam Hussein",           "Oligarchy",              200,  400, 0.78),
        "Ukraine":              ("Kyiv",             "Leonid Kuchma",            "Oligarchy",              360,  300, 0.48),
        "Poland":               ("Warsaw",           "Aleksander Kwaśniewski",   "Social Democracy",       450,  200, 0.36),
        "Spain":                ("Madrid",           "José María Aznar",         "Conservative Democracy", 800,  200, 0.36),
        "Sweden":               ("Stockholm",        "Göran Persson",            "Social Democracy",       410,   60, 0.24),
        "Cuba":                 ("Havana",           "Fidel Castro",             "Communism",               48,  100, 0.58),
        "Venezuela":            ("Caracas",          "Hugo Chávez",              "Socialism",              180,  100, 0.58),
        "Colombia":             ("Bogotá",           "Andrés Pastrana",          "Liberal Democracy",      240,  200, 0.46),
        "Thailand":             ("Bangkok",          "Chuan Leekpai",            "Liberal Democracy",      330,  300, 0.40),
        "Vietnam":              ("Hanoi",            "Trần Đức Lương",           "Communism",              120,  500, 0.50),
        "Taiwan":               ("Taipei",           "Chen Shui-bian",           "Liberal Democracy",      380,  290, 0.46),
        "Singapore":            ("Singapore",        "Goh Chok Tong",            "Liberal Democracy",      158,   72, 0.32),
    },
}

# Historical bilateral relations: (nation1, nation2) -> relation_score
_ERA_RELATIONS: dict[str, list[tuple[str, str, int]]] = {
    "1936": [
        ("Germany", "Italy", 45), ("Germany", "Japan", 40),
        ("Germany", "Soviet Union", -65), ("Germany", "France", -60),
        ("Germany", "United Kingdom", -45), ("Germany", "Poland", -55),
        ("Germany", "Czechoslovakia", -65), ("Germany", "United States", -30),
        ("France", "United Kingdom", 62), ("France", "Soviet Union", 18),
        ("France", "Poland", 42), ("France", "Czechoslovakia", 50),
        ("United Kingdom", "Canada", 75), ("United Kingdom", "Australia", 75),
        ("United Kingdom", "India", 25), ("United Kingdom", "South Africa", 55),
        ("Soviet Union", "China", 12), ("Soviet Union", "Japan", -55),
        ("Soviet Union", "Germany", -65), ("Soviet Union", "France", 18),
        ("Italy", "Ethiopia", -65), ("Japan", "China", -75),
        ("Japan", "United States", -28), ("Japan", "Soviet Union", -55),
        ("United States", "Canada", 82), ("United States", "United Kingdom", 52),
        ("United States", "France", 45), ("Hungary", "Germany", 35),
        ("Romania", "France", 30), ("Poland", "France", 42),
        ("Spain", "Germany", 30), ("Spain", "Italy", 28),
        ("Yugoslavia", "France", 25), ("Greece", "United Kingdom", 30),
    ],
    "1950": [
        ("United States", "United Kingdom", 75), ("United States", "France", 62),
        ("United States", "West Germany", 52), ("United States", "Japan", 58),
        ("United States", "Canada", 82), ("United States", "Australia", 76),
        ("United States", "Soviet Union", -72), ("United States", "China", -65),
        ("United States", "North Korea", -80), ("United States", "Cuba", -20),
        ("Soviet Union", "China", 48), ("Soviet Union", "North Korea", 65),
        ("Soviet Union", "Poland", 42), ("Soviet Union", "East Germany", 48),
        ("Soviet Union", "Czechoslovakia", 45), ("Soviet Union", "Yugoslavia", -22),
        ("China", "North Korea", 58), ("France", "United Kingdom", 65),
        ("France", "West Germany", 30), ("India", "Pakistan", -42),
        ("Israel", "Egypt", -65), ("Israel", "Jordan", -55),
        ("Canada", "Australia", 55), ("West Germany", "United Kingdom", 42),
        ("Italy", "France", 40), ("Italy", "United States", 48),
    ],
    "1980": [
        ("United States", "United Kingdom", 76), ("United States", "West Germany", 65),
        ("United States", "Japan", 62), ("United States", "Canada", 82),
        ("United States", "Australia", 72), ("United States", "Israel", 72),
        ("United States", "Soviet Union", -72), ("United States", "Iran", -78),
        ("United States", "Cuba", -78), ("United States", "Vietnam", -55),
        ("Soviet Union", "East Germany", 62), ("Soviet Union", "Cuba", 58),
        ("Soviet Union", "Vietnam", 48), ("Soviet Union", "China", -35),
        ("Soviet Union", "Afghanistan", 30), ("Iran", "Iraq", -78),
        ("Israel", "Egypt", 18), ("Israel", "Syria", -65),
        ("India", "Pakistan", -48), ("India", "Soviet Union", 35),
        ("North Korea", "South Korea", -82), ("North Korea", "China", 45),
        ("Argentina", "United Kingdom", -42), ("Libya", "Egypt", -30),
        ("Syria", "Iraq", -35), ("Iraq", "Iran", -78),
        ("France", "West Germany", 62), ("France", "United Kingdom", 55),
        ("Spain", "United States", 40), ("Spain", "France", 42),
    ],
    "2000": [
        ("United States", "United Kingdom", 76), ("United States", "Canada", 84),
        ("United States", "Australia", 74), ("United States", "Japan", 66),
        ("United States", "Germany", 62), ("United States", "France", 55),
        ("United States", "Israel", 74), ("United States", "South Korea", 58),
        ("United States", "Russia", -28), ("United States", "China", -18),
        ("United States", "Iraq", -72), ("United States", "North Korea", -82),
        ("United States", "Iran", -68), ("United States", "Cuba", -72),
        ("Russia", "China", 38), ("Russia", "Ukraine", 18),
        ("Russia", "Belarus", 55), ("Russia", "Serbia", 42),
        ("China", "North Korea", 42), ("China", "Taiwan", -68),
        ("China", "Vietnam", -20), ("India", "Pakistan", -52),
        ("India", "Russia", 38), ("Israel", "Iran", -72),
        ("Israel", "Egypt", 28), ("Israel", "Jordan", 32),
        ("Germany", "France", 74), ("Germany", "United Kingdom", 60),
        ("Germany", "Poland", 40), ("Brazil", "Argentina", 42),
        ("Saudi Arabia", "Iraq", -35), ("Iran", "Iraq", -55),
        ("Venezuela", "Cuba", 50), ("Venezuela", "United States", -30),
    ],
}

# Population estimates (base for 1936 era; scaled by era multiplier)
_POPULATION_BASE: dict[str, int] = {
    "China": 500_000_000, "India": 350_000_000, "Soviet Union": 160_000_000,
    "United States": 127_000_000, "Brazil": 40_000_000, "Germany": 66_000_000,
    "Japan": 69_000_000, "United Kingdom": 47_000_000, "France": 41_000_000,
    "Italy": 42_000_000, "Canada": 11_000_000, "Australia": 7_000_000,
    "Poland": 35_000_000, "Romania": 19_000_000, "Turkey": 17_000_000,
    "Mexico": 18_000_000, "Argentina": 14_000_000, "Egypt": 16_000_000,
    "Iran": 15_000_000, "Iraq": 4_000_000, "Saudi Arabia": 2_000_000,
    "Sweden": 6_000_000, "Norway": 3_000_000, "Denmark": 4_000_000,
    "Finland": 3_600_000, "Belgium": 8_300_000, "Netherlands": 8_700_000,
    "Switzerland": 4_200_000, "Spain": 24_000_000, "Portugal": 7_000_000,
    "Ethiopia": 12_000_000, "South Africa": 10_000_000, "Nigeria": 20_000_000,
    "Yugoslavia": 15_000_000, "Czechoslovakia": 15_000_000, "Hungary": 9_200_000,
    "Austria": 6_700_000, "Greece": 7_200_000, "Bulgaria": 6_000_000,
    "Libya": 750_000, "Syria": 2_500_000, "Indonesia": 60_000_000,
    "Pakistan": 28_000_000, "Vietnam": 19_000_000, "North Korea": 8_000_000,
    "South Korea": 20_000_000, "Taiwan": 6_000_000, "Singapore": 1_000_000,
    "Israel": 1_000_000, "Cuba": 5_000_000, "Venezuela": 4_000_000,
    "Colombia": 9_000_000, "Thailand": 18_000_000, "Ukraine": 30_000_000,
}

_ERA_POP_MULT = {"1936": 1.0, "1950": 1.18, "1980": 1.72, "2000": 2.05}

_IDEOLOGY_GOVT_TYPE = {
    "Liberal Democracy":      "Federal Republic",
    "Social Democracy":       "Parliamentary Republic",
    "Conservative Democracy": "Constitutional Republic",
    "Socialism":              "Socialist Republic",
    "Communism":              "People's Republic",
    "Fascism":                "Fascist State",
    "Monarchy":               "Constitutional Monarchy",
    "Theocracy":              "Islamic Republic",
    "Technocracy":            "Technocratic Council",
    "Oligarchy":              "Presidential Republic",
}

_IDEOLOGY_PERSONA = {
    "Liberal Democracy":      {"aggression": 0.30, "econ": "trade",    "diplo": "cooperative"},
    "Social Democracy":       {"aggression": 0.26, "econ": "welfare",  "diplo": "cooperative"},
    "Conservative Democracy": {"aggression": 0.38, "econ": "balanced", "diplo": "cautious"},
    "Socialism":              {"aggression": 0.46, "econ": "state",    "diplo": "neutral"},
    "Communism":              {"aggression": 0.65, "econ": "industry", "diplo": "bloc"},
    "Fascism":                {"aggression": 0.82, "econ": "military", "diplo": "expansionist"},
    "Monarchy":               {"aggression": 0.50, "econ": "balanced", "diplo": "traditional"},
    "Theocracy":              {"aggression": 0.55, "econ": "state",    "diplo": "isolationist"},
    "Technocracy":            {"aggression": 0.33, "econ": "industry", "diplo": "cooperative"},
    "Oligarchy":              {"aggression": 0.56, "econ": "elite",    "diplo": "transactional"},
}

_IDEOLOGY_GRIEVANCES = {
    "Fascism":       ["unfair post-war settlement", "ethnic homeland denied", "expansionist destiny unfulfilled"],
    "Communism":     ["capitalist exploitation", "imperialist interference", "class oppression by elites"],
    "Monarchy":      ["republican revolution threat", "dynastic rivals", "colonial pressure from democracies"],
    "Theocracy":     ["secular imperialism", "foreign moral corruption", "persecution of the faithful"],
    "Oligarchy":     ["foreign sanctions", "trade imbalance", "resource competition"],
    "Liberal Democracy": ["authoritarian neighbor aggression", "arms race pressure"],
    "Social Democracy":  ["capitalist inequality", "military spending demands"],
    "Socialism":     ["corporate neo-colonialism", "western financial domination"],
}

_IDEO_ALIGNMENT: dict[tuple[str, str], int] = {}  # cache built lazily


def _ideo_relation_bonus(ideo1: str, ideo2: str) -> int:
    key = (ideo1, ideo2)
    if key in _IDEO_ALIGNMENT:
        return _IDEO_ALIGNMENT[key]
    demo = {"Liberal Democracy", "Social Democracy", "Conservative Democracy"}
    auth = {"Fascism", "Communism", "Oligarchy", "Theocracy", "Monarchy"}
    if ideo1 == ideo2:
        val = random.randint(12, 22)
    elif ideo1 in demo and ideo2 in demo:
        val = random.randint(8, 16)
    elif ideo1 in auth and ideo2 in auth:
        val = random.randint(4, 12)
    elif (ideo1 in demo and ideo2 in auth) or (ideo1 in auth and ideo2 in demo):
        val = random.randint(-22, -8)
    else:
        val = random.randint(-5, 5)
    _IDEO_ALIGNMENT[key] = val
    return val


def _estimate_population(name: str, era_id: str) -> int:
    base = _POPULATION_BASE.get(name, random.randint(5_000_000, 40_000_000))
    mult = _ERA_POP_MULT.get(era_id, 1.0)
    return int(base * mult * random.uniform(0.92, 1.08))


def _get_nation_data(name: str, era_id: str) -> dict:
    era_table = _ERA_NATION_DATA.get(era_id, _ERA_NATION_DATA["1936"])
    hist = era_table.get(name)

    if hist:
        capital, leader, ideology, gdp_b, army_k, aggression = hist
    else:
        ideology = "Liberal Democracy"
        capital = name.split()[0] + " City" if " " in name else name
        leader = f"President of {name}"
        gdp_b = random.randint(10, 150)
        army_k = int(gdp_b * random.uniform(0.4, 1.4))
        aggression = random.uniform(0.35, 0.60)

    p = _IDEOLOGY_PERSONA.get(ideology, _IDEOLOGY_PERSONA["Liberal Democracy"])
    aggression = max(0.18, min(0.92, aggression + random.uniform(-0.05, 0.05)))
    pop = _estimate_population(name, era_id)
    stability   = round(max(0.35, min(0.92, 0.70 + random.uniform(-0.18, 0.15))), 2)
    war_support = round(max(0.28, min(0.88, 0.50 + (aggression - 0.5) * 0.4 + random.uniform(-0.08, 0.08))), 2)
    gdp_growth  = round(max(-0.04, min(0.10, 0.03 + random.uniform(-0.025, 0.04))), 4)
    unemployment = round(max(0.02, min(0.28, 0.08 + random.uniform(-0.04, 0.09))), 3)
    inflation   = round(max(0.00, min(0.18, 0.03 + random.uniform(-0.02, 0.06))), 3)
    grievances  = _IDEOLOGY_GRIEVANCES.get(ideology, [])
    grievances  = random.sample(grievances, min(2, len(grievances)))

    return {
        "capital":        capital,
        "leader":         leader,
        "ideology":       ideology,
        "government_type": _IDEOLOGY_GOVT_TYPE.get(ideology, "Republic"),
        "population":     pop,
        "stability":      stability,
        "war_support":    war_support,
        "prestige":       round(max(20, min(150, gdp_b / 3 + aggression * 28 + random.uniform(-8, 8))), 1),
        "economy": {
            "gdp":            gdp_b * 1_000_000_000,
            "gdp_growth":     gdp_growth,
            "unemployment":   unemployment,
            "inflation":      inflation,
            "trade_openness": round(max(0.10, min(0.90, 0.50 + (0.50 - aggression) * 0.30)), 2),
            "trade_balance":  round(random.uniform(-5, 8), 2),
            "industry_output": max(10, int(gdp_b * 0.25 + random.uniform(-5, 15))),
            "factories":      max(5,  int(gdp_b / 14)),
            "arms_factories": max(1,  int(gdp_b / 55 * aggression * 2)),
            "research_labs":  max(1,  int(gdp_b / 75)),
            "stockpile": {
                "steel":     max(0, int(gdp_b * 0.80 + random.uniform(-20, 20))),
                "fuel":      max(0, int(gdp_b * 0.60 + random.uniform(-20, 20))),
                "equipment": max(0, int(army_k * 0.30 + random.uniform(-10, 10))),
            },
        },
        "military": {
            "army_size":       army_k * 1000,
            "equipment_level": round(max(0.30, min(1.0, 0.65 + (aggression - 0.5) * 0.30)), 2),
            "morale":          round(max(0.40, min(1.0,  0.72 + random.uniform(-0.15, 0.15))), 2),
            "military_spending": round(max(0.02, min(0.16, 0.04 + aggression * 0.06)), 3),
            "navy_tonnage":    int(army_k * random.uniform(0.20, 0.80)),
            "air_force":       int(army_k * random.uniform(0.05, 0.25)),
            "manpower_pool":   int(pop * 0.05),
        },
        "diplomacy": {
            "alliances": [], "defense_pacts": [], "trade_deals": [],
            "sanctions_against": [], "relations": {},
        },
        "personality": {
            "aggression":            round(aggression, 2),
            "economic_priority":     p["econ"],
            "diplomatic_tendency":   p["diplo"],
            "historical_grievances": grievances,
            "core_claims":           [],
        },
    }


def _seed_starting_alliances(nations: dict):
    pairs = [
        ("United States", "United Kingdom"), ("United States", "Canada"),
        ("United States", "Australia"), ("France", "United Kingdom"),
        ("Germany", "Italy"), ("Germany", "Japan"),
        ("Soviet Union", "China"), ("China", "North Korea"),
        ("West Germany", "France"), ("West Germany", "United Kingdom"),
        ("Brazil", "Argentina"),
    ]
    for n1, n2 in pairs:
        if n1 in nations and n2 in nations:
            rel = nations[n1]["diplomacy"]["relations"].get(n2, 0)
            if rel > 38:
                if n2 not in nations[n1]["diplomacy"]["alliances"]:
                    nations[n1]["diplomacy"]["alliances"].append(n2)
                if n1 not in nations[n2]["diplomacy"]["alliances"]:
                    nations[n2]["diplomacy"]["alliances"].append(n1)


async def generate_world_state(era_id: str, era_name: str, player_nation: str,
                               ideology: str, major_nations: list[str]) -> dict:
    """Procedural world builder — instant, historically informed, zero network."""
    nations_out: dict[str, dict] = {}
    for name in major_nations:
        nations_out[name] = _get_nation_data(name, era_id)

    # Apply historical bilateral relations
    for n1, n2, bonus in _ERA_RELATIONS.get(era_id, []):
        if n1 in nations_out and n2 in nations_out:
            j = random.randint(-8, 8)
            for a, b in ((n1, n2), (n2, n1)):
                cur = nations_out[a]["diplomacy"]["relations"].get(b, 0)
                nations_out[a]["diplomacy"]["relations"][b] = max(-100, min(100, cur + bonus + j))

    # Fill remaining pairs with ideology-based defaults
    for n1, d1 in nations_out.items():
        for n2, d2 in nations_out.items():
            if n1 == n2:
                continue
            if n2 not in d1["diplomacy"]["relations"]:
                bonus = _ideo_relation_bonus(d1["ideology"], d2["ideology"])
                base  = random.randint(-12, 12) + bonus
                d1["diplomacy"]["relations"][n2] = max(-65, min(65, base))

    _seed_starting_alliances(nations_out)

    avg_agg = sum(d["personality"]["aggression"] for d in nations_out.values()) / max(1, len(nations_out))
    world_tension = round(max(0.15, min(0.80, avg_agg * 0.70 + random.uniform(-0.05, 0.10))), 2)

    print(f"[NPC-Engine] World generated: {len(nations_out)} nations, tension={world_tension:.0%}")
    return {"nations": nations_out, "world_tension": world_tension}


# ── Nation AI Decisions ───────────────────────────────────────────────────────

async def generate_nation_decision(game_state_summary: dict, nation_id: str) -> dict:
    return _smart_decision(game_state_summary, nation_id)


def _smart_decision(gs: dict, nation_id: str) -> dict:
    """
    Multi-factor, ideology-aware NPC decision engine.
    Returns {"actions": [...]} exactly like the old AI call did.
    """
    nation = gs["nations"].get(nation_id, {})
    if not nation:
        return {"actions": []}

    ideology  = nation.get("ideology", "Liberal Democracy")
    eco       = nation.get("economy", {})
    mil       = nation.get("military", {})
    pers      = nation.get("personality", {})
    diplo     = nation.get("diplomacy", {})
    tension   = gs.get("world_tension", 0.30)
    player_id = gs.get("player_nation_id", "")

    agg          = pers.get("aggression", 0.50)
    gdp_growth   = eco.get("gdp_growth", 0.03)
    stability    = nation.get("stability", 0.70)
    army_size    = mil.get("army_size", 100_000)
    relations    = diplo.get("relations", {})
    alliances    = diplo.get("alliances", [])
    is_at_war    = nation.get("is_at_war", False)
    actions: list[dict] = []

    # ── Internal crises override geopolitics ─────────────────────────
    if gdp_growth < 0.0 or stability < 0.42:
        if random.random() < 0.65:
            actions.append({"action": "boost_economy", "target": None, "reason": "crisis recovery"})
        return {"actions": actions[:2]}

    # ── Wartime logic ────────────────────────────────────────────────
    if is_at_war:
        if army_size < 250_000 and random.random() < 0.72:
            actions.append({"action": "build_army", "target": None, "reason": "war mobilization"})
        if alliances and random.random() < 0.35:
            ally = random.choice([a for a in alliances if a != player_id] or [None])
            if ally:
                ally_name = gs["nations"].get(ally, {}).get("name")
                if ally_name:
                    actions.append({"action": "improve_relations", "target": ally_name, "reason": "wartime solidarity"})
        return {"actions": actions[:2]}

    # ── Ideology branches ────────────────────────────────────────────
    if ideology == "Fascism":
        if random.random() < 0.58:
            actions.append({"action": "build_army", "target": None, "reason": "military buildup"})
        if tension > 0.48 and agg > 0.72 and random.random() < 0.28:
            target = _find_war_target(gs, nation_id)
            if target:
                actions.append({"action": "declare_war", "target": target, "reason": "territorial expansion"})
        elif random.random() < 0.28:
            t = _best_diplo_target(relations, alliances, player_id, gs, ideology, "ideological")
            if t:
                actions.append({"action": "improve_relations", "target": t, "reason": "fascist solidarity"})

    elif ideology == "Communism":
        if random.random() < 0.42:
            actions.append({"action": "build_army", "target": None, "reason": "proletarian defense"})
        if random.random() < 0.42:
            t = _best_diplo_target(relations, alliances, player_id, gs, ideology, "ideological")
            if t:
                actions.append({"action": "improve_relations", "target": t, "reason": "communist bloc"})
        if tension > 0.60 and agg > 0.68 and random.random() < 0.18:
            target = _find_war_target(gs, nation_id)
            if target:
                actions.append({"action": "declare_war", "target": target, "reason": "socialist liberation"})

    elif ideology in ("Liberal Democracy", "Social Democracy"):
        if random.random() < 0.58:
            t = _best_diplo_target(relations, alliances, player_id, gs, ideology, "friendly")
            if t:
                actions.append({"action": "improve_relations", "target": t, "reason": "diplomatic outreach"})
        if random.random() < 0.32 and gdp_growth > 0.01:
            actions.append({"action": "boost_economy", "target": None, "reason": "prosperity agenda"})
        if random.random() < 0.22:
            t = _find_alliance_candidate(relations, alliances, player_id, gs, ideology)
            if t:
                actions.append({"action": "form_alliance", "target": t, "reason": "mutual security"})

    elif ideology == "Conservative Democracy":
        if random.random() < 0.42:
            t = _best_diplo_target(relations, alliances, player_id, gs, ideology, "friendly")
            if t:
                actions.append({"action": "improve_relations", "target": t, "reason": "strengthening ties"})
        if random.random() < 0.32 and army_size < 500_000:
            actions.append({"action": "build_army", "target": None, "reason": "national defense"})

    elif ideology == "Monarchy":
        if random.random() < 0.48:
            t = _best_diplo_target(relations, alliances, player_id, gs, ideology, "traditional")
            if t:
                actions.append({"action": "improve_relations", "target": t, "reason": "dynastic ties"})
        if agg > 0.62 and tension > 0.42 and random.random() < 0.18:
            target = _find_war_target(gs, nation_id)
            if target:
                actions.append({"action": "declare_war", "target": target, "reason": "imperial expansion"})

    elif ideology in ("Oligarchy", "Theocracy"):
        if random.random() < 0.42:
            actions.append({"action": "build_army", "target": None, "reason": "regime security"})
        if random.random() < 0.38:
            t = _best_diplo_target(relations, alliances, player_id, gs, ideology, "friendly")
            if t:
                actions.append({"action": "improve_relations", "target": t, "reason": "strategic partnership"})

    else:
        if random.random() < 0.52:
            t = _best_diplo_target(relations, alliances, player_id, gs, ideology, "friendly")
            if t:
                actions.append({"action": "improve_relations", "target": t, "reason": "regional stability"})
        if gdp_growth < 0.02 and random.random() < 0.42:
            actions.append({"action": "boost_economy", "target": None, "reason": "development"})

    if not actions:
        actions.append({"action": "boost_economy", "target": None, "reason": "domestic investment"})

    return {"actions": actions[:2]}


def _find_war_target(gs: dict, nation_id: str) -> str | None:
    nation = gs["nations"].get(nation_id, {})
    relations  = nation.get("diplomacy", {}).get("relations", {})
    alliances  = nation.get("diplomacy", {}).get("alliances", [])
    player_id  = gs.get("player_nation_id", "")
    my_army    = nation.get("military", {}).get("army_size", 100_000)

    best_score, best_name = -999, None
    for nid, n in gs["nations"].items():
        if nid in (nation_id, player_id):
            continue
        if not n.get("is_alive", True) or n.get("is_at_war", False):
            continue
        if nid in alliances:
            continue
        rel = relations.get(nid, 0)
        if rel > -8:
            continue
        their_army = n.get("military", {}).get("army_size", 100_000)
        ratio = my_army / max(1, their_army)
        if ratio < 0.75:
            continue  # don't attack much stronger nations
        score = -rel + ratio * 12 + random.uniform(-5, 5)
        if score > best_score:
            best_score, best_name = score, n.get("name", nid)
    return best_name


def _best_diplo_target(relations: dict, alliances: list, player_id: str,
                       gs: dict, ideology: str, style: str) -> str | None:
    demo = {"Liberal Democracy", "Social Democracy", "Conservative Democracy"}
    auth = {"Fascism", "Communism", "Oligarchy", "Monarchy", "Theocracy"}
    best_score, best_name = -999, None
    for nid, n in gs["nations"].items():
        if nid == player_id or not n.get("is_alive", True):
            continue
        rel = relations.get(nid, 0)
        if rel >= 90:
            continue
        tideo = n.get("ideology", "")
        score = rel * 0.25 + random.uniform(-6, 6)
        if style == "ideological":
            score += 32 if tideo == ideology else 0
        elif style == "friendly":
            score += 18 if tideo == ideology else 0
            score += 10 if ideology in demo and tideo in demo else 0
            score += 8  if ideology in auth and tideo in auth else 0
        elif style == "traditional":
            score += rel * 0.45
        if score > best_score:
            best_score, best_name = score, n.get("name", nid)
    return best_name


def _find_alliance_candidate(relations: dict, alliances: list, player_id: str,
                              gs: dict, ideology: str) -> str | None:
    demo = {"Liberal Democracy", "Social Democracy", "Conservative Democracy"}
    for nid, n in gs["nations"].items():
        if nid == player_id or nid in alliances or not n.get("is_alive", True):
            continue
        if relations.get(nid, 0) < 55:
            continue
        if ideology in demo and n.get("ideology", "") in demo:
            return n.get("name", nid)
    return None


# ── Issue Pool ────────────────────────────────────────────────────────────────

_ISSUES: dict[str, list[dict]] = {
    "economic": [
        {"title": "Labor Strike Threatens Industry",
         "description": "Factory workers demand higher wages and better conditions. Production has halted.",
         "urgency": "high",
         "options": [
             {"id": 1, "text": "Grant wage increases.", "effects": {"stability": 0.05, "gdp_growth": -0.01, "unemployment": -0.02}, "flavor": "Workers return satisfied."},
             {"id": 2, "text": "Deploy police — break the strike by force.", "effects": {"stability": -0.08, "war_support": 0.03, "prestige": -5}, "flavor": "Crushed, but resentment lingers."},
             {"id": 3, "text": "Negotiate a compromise deal.", "effects": {"stability": 0.02, "gdp_growth": 0.005}, "flavor": "Cautious deal keeps factories running."},
         ]},
        {"title": "Economic Recession Looms",
         "description": "GDP growth stalls and unemployment rises. Economists warn of impending recession.",
         "urgency": "high",
         "options": [
             {"id": 1, "text": "Stimulus spending on infrastructure.", "effects": {"gdp_growth": 0.02, "unemployment": -0.03, "inflation": 0.02}, "flavor": "Growth returns; prices rise."},
             {"id": 2, "text": "Austerity — cut government spending drastically.", "effects": {"gdp_growth": -0.01, "stability": -0.05, "inflation": -0.01}, "flavor": "Budgets balance; suffering increases."},
             {"id": 3, "text": "Invite foreign investment with tax breaks.", "effects": {"gdp_growth": 0.015, "prestige": 3}, "flavor": "Foreign capital floods in."},
         ]},
        {"title": "Currency Shock",
         "description": "Foreign investors are dumping the national currency. Inflation fears spiral.",
         "urgency": "high",
         "options": [
             {"id": 1, "text": "Raise interest rates sharply.", "effects": {"inflation": -0.01, "gdp_growth": -0.01}, "flavor": "Currency stabilizes; growth slows."},
             {"id": 2, "text": "Impose capital controls.", "effects": {"stability": 0.02, "prestige": -4}, "flavor": "Markets calm; reputation suffers."},
             {"id": 3, "text": "Let the currency float freely.", "effects": {"gdp_growth": 0.005, "inflation": 0.01}, "flavor": "Exports surge; prices rise."},
         ]},
        {"title": "Oil Price Shock",
         "description": "Global oil prices surge. Fuel costs cripple transport and industry.",
         "urgency": "high",
         "options": [
             {"id": 1, "text": "Subsidize fuel for citizens and industry.", "effects": {"stability": 0.04, "gdp_growth": -0.015}, "flavor": "Crisis absorbed; budget strains."},
             {"id": 2, "text": "Let market prices rise. Encourage conservation.", "effects": {"stability": -0.05, "gdp_growth": 0.005, "inflation": 0.02}, "flavor": "Efficiency improves; protests erupt."},
             {"id": 3, "text": "Invest in alternative energy sources.", "effects": {"gdp_growth": 0.005, "prestige": 5}, "flavor": "Long-term fix; short-term pain."},
         ]},
        {"title": "Factory Modernization Program",
         "description": "Industrial leaders demand subsidies to upgrade aging factories.",
         "urgency": "normal",
         "options": [
             {"id": 1, "text": "Fund full modernization program.", "effects": {"gdp_growth": 0.02, "unemployment": 0.02}, "flavor": "Output soars; workers displaced."},
             {"id": 2, "text": "Partial funding with worker retraining.", "effects": {"gdp_growth": 0.01, "stability": 0.02}, "flavor": "Balance carefully struck."},
             {"id": 3, "text": "Reject subsidy — market decides.", "effects": {"prestige": 3, "gdp_growth": -0.005}, "flavor": "Factories lag; deficit avoided."},
         ]},
        {"title": "Rail Network Overload",
         "description": "Freight lines are jammed. Export delays cost millions monthly.",
         "urgency": "normal",
         "options": [
             {"id": 1, "text": "Fund new rail construction.", "effects": {"gdp_growth": 0.01, "stability": 0.01}, "flavor": "Trade speeds up."},
             {"id": 2, "text": "Shift freight to trucks temporarily.", "effects": {"gdp_growth": 0.005, "inflation": 0.01}, "flavor": "Short-term fix; higher fuel costs."},
             {"id": 3, "text": "Impose export quotas until upgrades complete.", "effects": {"gdp_growth": -0.01, "stability": 0.02}, "flavor": "Prices stabilize; exporters fume."},
         ]},
        {"title": "Food Price Crisis",
         "description": "Crop failures drive food prices to record highs. Urban unrest spreads.",
         "urgency": "high",
         "options": [
             {"id": 1, "text": "Emergency food imports.", "effects": {"stability": 0.05, "gdp_growth": -0.01}, "flavor": "Famine averted at economic cost."},
             {"id": 2, "text": "Nationalize food distribution. Ration strictly.", "effects": {"stability": -0.02, "war_support": -0.04}, "flavor": "Order maintained; morale drops."},
             {"id": 3, "text": "Invest in irrigation and modern farming.", "effects": {"gdp_growth": 0.01, "stability": 0.02}, "flavor": "Long-term fix; citizens suffer now."},
         ]},
        {"title": "Trade Union Power Struggle",
         "description": "Competing union factions cause wildcat strikes across key industries.",
         "urgency": "high",
         "options": [
             {"id": 1, "text": "Officially recognize the dominant union.", "effects": {"stability": 0.04, "gdp_growth": -0.005}, "flavor": "Order restored with labor peace."},
             {"id": 2, "text": "Break up all unions. Outlaw collective bargaining.", "effects": {"stability": -0.08, "war_support": 0.05, "gdp_growth": 0.01}, "flavor": "Production resumes; unrest deepens."},
             {"id": 3, "text": "Force merger of both factions through mediation.", "effects": {"stability": 0.02, "gdp_growth": 0.005}, "flavor": "Fragile peace holds."},
         ]},
    ],
    "political": [
        {"title": "Corruption Scandal Rocks Cabinet",
         "description": "Leaked documents reveal officials accepting bribes. Public trust collapses.",
         "urgency": "critical",
         "options": [
             {"id": 1, "text": "Launch full public inquiry. Prosecute all.", "effects": {"stability": 0.08, "prestige": 10, "gdp_growth": -0.01}, "flavor": "Accountability restores faith slowly."},
             {"id": 2, "text": "Cover it up. Blame enemy propaganda.", "effects": {"stability": -0.10, "prestige": -15, "war_support": -0.05}, "flavor": "The cover-up leaks — it gets worse."},
             {"id": 3, "text": "Quietly reassign officials. Keep it private.", "effects": {"stability": -0.02, "prestige": -5}, "flavor": "Bought time; problem festers."},
         ]},
        {"title": "Press Freedom Controversy",
         "description": "Opposition newspapers publish scathing critiques of government policy.",
         "urgency": "normal",
         "options": [
             {"id": 1, "text": "Guarantee full press freedom.", "effects": {"stability": 0.04, "prestige": 8, "war_support": -0.03}, "flavor": "Democracy strengthened; critics louder."},
             {"id": 2, "text": "Impose censorship. Control the narrative.", "effects": {"stability": 0.02, "prestige": -12, "war_support": 0.05}, "flavor": "Dissent silenced; resentment grows."},
             {"id": 3, "text": "Regulate 'national security' content only.", "effects": {"stability": 0.01, "prestige": -3}, "flavor": "Compromise pleases no one."},
         ]},
        {"title": "Political Assassination Attempt",
         "description": "A senior official narrowly survives an assassination attempt. Security is shaken.",
         "urgency": "critical",
         "options": [
             {"id": 1, "text": "Declare state of emergency. Mass crackdown.", "effects": {"stability": -0.05, "war_support": 0.08, "prestige": -3}, "flavor": "Streets calm; fear spreads."},
             {"id": 2, "text": "Pursue suspects through normal legal channels.", "effects": {"stability": 0.03, "prestige": 6}, "flavor": "Rule of law upheld."},
             {"id": 3, "text": "Blame foreign agents. Use it politically.", "effects": {"war_support": 0.10, "prestige": -5, "stability": 0.02}, "flavor": "Nationalists rally; truth suppressed."},
         ]},
        {"title": "Constitutional Crisis",
         "description": "A dispute between parliament and executive threatens to paralyze government.",
         "urgency": "critical",
         "options": [
             {"id": 1, "text": "Call snap elections to reset the mandate.", "effects": {"stability": 0.06, "prestige": 5, "gdp_growth": -0.01}, "flavor": "Democratic process wins out."},
             {"id": 2, "text": "Dissolve parliament. Rule by decree.", "effects": {"stability": -0.10, "war_support": 0.05, "prestige": -12}, "flavor": "Crisis solved; democracy damaged."},
             {"id": 3, "text": "Negotiate a power-sharing coalition deal.", "effects": {"stability": 0.04, "prestige": 3}, "flavor": "Compromise holds fragile balance."},
         ]},
        {"title": "Cybersecurity Breach",
         "description": "A major data breach exposes government systems and citizen records.",
         "urgency": "high",
         "options": [
             {"id": 1, "text": "Create a national cyber defense agency.", "effects": {"stability": 0.02, "prestige": 4, "gdp_growth": -0.005}, "flavor": "Security improves over time."},
             {"id": 2, "text": "Outsource to private security firms.", "effects": {"prestige": 2, "gdp_growth": 0.003}, "flavor": "Fast response; accountability questioned."},
             {"id": 3, "text": "Downplay the incident and move on.", "effects": {"stability": -0.03, "prestige": -5}, "flavor": "Public trust erodes."},
         ]},
        {"title": "Electoral Fraud Allegations",
         "description": "Opposition parties accuse the government of rigging local elections.",
         "urgency": "high",
         "options": [
             {"id": 1, "text": "Order an independent electoral audit.", "effects": {"stability": 0.05, "prestige": 8}, "flavor": "Transparency wins public trust."},
             {"id": 2, "text": "Dismiss as foreign interference.", "effects": {"stability": -0.06, "prestige": -8}, "flavor": "Protests intensify."},
             {"id": 3, "text": "Offer partial recount as limited concession.", "effects": {"stability": 0.02, "prestige": 2}, "flavor": "Tensions cool slightly."},
         ]},
    ],
    "social": [
        {"title": "Refugee Crisis at the Border",
         "description": "Thousands of displaced civilians mass at the border, fleeing neighboring conflict.",
         "urgency": "high",
         "options": [
             {"id": 1, "text": "Open the border. Full support for refugees.", "effects": {"stability": -0.03, "prestige": 8, "gdp_growth": 0.005}, "flavor": "International praise; resources strained."},
             {"id": 2, "text": "Close the border. Refuse entry.", "effects": {"stability": 0.02, "prestige": -10, "war_support": 0.05}, "flavor": "Nationalists cheer; world condemns."},
             {"id": 3, "text": "Establish transit camps with international aid.", "effects": {"stability": 0.01, "prestige": 3, "gdp_growth": -0.005}, "flavor": "Measured response satisfies no one."},
         ]},
        {"title": "Veterans Demand Benefits",
         "description": "War veterans march in the capital demanding expanded pensions and healthcare.",
         "urgency": "high",
         "options": [
             {"id": 1, "text": "Expand veteran benefits immediately.", "effects": {"happiness": 0.04, "stability": 0.03, "gdp_growth": -0.01}, "flavor": "Support rises; budget tightens."},
             {"id": 2, "text": "Offer phased reforms over five years.", "effects": {"happiness": 0.02, "stability": 0.01}, "flavor": "Some satisfied; protests continue."},
             {"id": 3, "text": "Refuse new spending. Redirect funds.", "effects": {"happiness": -0.04, "stability": -0.03}, "flavor": "Demonstrations spread."},
         ]},
        {"title": "Public Healthcare Crisis",
         "description": "Hospitals overwhelmed. Waiting lists at record highs. Doctors threaten to strike.",
         "urgency": "high",
         "options": [
             {"id": 1, "text": "Emergency healthcare funding increase.", "effects": {"stability": 0.05, "happiness": 0.04, "gdp_growth": -0.015}, "flavor": "Crisis eased; deficit grows."},
             {"id": 2, "text": "Privatize portions of the system.", "effects": {"gdp_growth": 0.01, "stability": -0.04, "prestige": -3}, "flavor": "Efficiency rises; public outrage."},
             {"id": 3, "text": "Import foreign medical professionals.", "effects": {"stability": 0.02, "happiness": 0.02}, "flavor": "Gap bridged; long-term issues remain."},
         ]},
        {"title": "Youth Unemployment Surge",
         "description": "A generation cannot find work. Universities overflow; streets grow restless.",
         "urgency": "high",
         "options": [
             {"id": 1, "text": "National job creation program.", "effects": {"unemployment": -0.04, "gdp_growth": -0.01, "stability": 0.04}, "flavor": "Youth employed; deficit climbs."},
             {"id": 2, "text": "Subsidize entrepreneurship and startups.", "effects": {"gdp_growth": 0.015, "unemployment": -0.02}, "flavor": "Innovation booms long-term."},
             {"id": 3, "text": "Expand military conscription.", "effects": {"unemployment": -0.03, "war_support": 0.06, "stability": -0.02}, "flavor": "Absorbed; society militarizes."},
         ]},
        {"title": "Drug Epidemic",
         "description": "Synthetic drugs flood cities. Overdose deaths reach crisis levels.",
         "urgency": "high",
         "options": [
             {"id": 1, "text": "War on drugs: mass arrests and harsh sentences.", "effects": {"stability": 0.02, "happiness": -0.03, "prestige": -2}, "flavor": "Crime down; prisons overflow."},
             {"id": 2, "text": "Legalize and regulate. Tax revenue funds treatment.", "effects": {"gdp_growth": 0.01, "happiness": 0.03, "prestige": 3}, "flavor": "Bold move; results gradual."},
             {"id": 3, "text": "Massive public health and rehabilitation program.", "effects": {"stability": 0.04, "happiness": 0.04, "gdp_growth": -0.01}, "flavor": "Compassionate; results slow."},
         ]},
        {"title": "Cultural Heritage Dispute",
         "description": "A foreign power demands return of artifacts removed during colonial era.",
         "urgency": "normal",
         "options": [
             {"id": 1, "text": "Return the artifacts diplomatically.", "effects": {"prestige": 10, "stability": 0.02}, "flavor": "International goodwill earned."},
             {"id": 2, "text": "Refuse — the artifacts are legally ours.", "effects": {"prestige": -5, "stability": 0.01}, "flavor": "Nationalists pleased; relations sour."},
             {"id": 3, "text": "Offer high-quality replicas. Retain originals.", "effects": {"prestige": 2, "stability": 0.01}, "flavor": "Diplomatic fudge satisfies neither."},
         ]},
    ],
    "military": [
        {"title": "Military Modernization Debate",
         "description": "High command demands new weapons. Treasury warns the budget cannot sustain it.",
         "urgency": "normal",
         "options": [
             {"id": 1, "text": "Approve full military expansion.", "effects": {"war_support": 0.08, "stability": -0.02, "gdp_growth": -0.015}, "flavor": "Army modernizes; economy strains."},
             {"id": 2, "text": "Reject — prioritize domestic investment.", "effects": {"stability": 0.03, "gdp_growth": 0.01, "war_support": -0.05}, "flavor": "Generals furious; civilians applaud."},
             {"id": 3, "text": "Partial upgrade — one branch only.", "effects": {"war_support": 0.03, "gdp_growth": -0.005}, "flavor": "Compromise satisfies no one."},
         ]},
        {"title": "Arms Factory Explosion",
         "description": "An explosion at a major arms plant halts production and sparks safety protests.",
         "urgency": "high",
         "options": [
             {"id": 1, "text": "Invest heavily in safety upgrades.", "effects": {"stability": 0.02, "gdp_growth": -0.005}, "flavor": "Output recovers safely."},
             {"id": 2, "text": "Press full production — ignore safety concerns.", "effects": {"war_support": 0.03, "stability": -0.03}, "flavor": "Output rises; unrest grows."},
             {"id": 3, "text": "Shift to private contractors.", "effects": {"gdp_growth": 0.004, "prestige": -2}, "flavor": "Costs fall; oversight weakens."},
         ]},
        {"title": "Military Coup Threat",
         "description": "Rumors of a military faction planning to seize power. Officers are restless.",
         "urgency": "critical",
         "options": [
             {"id": 1, "text": "Purge suspected plotters immediately.", "effects": {"stability": 0.04, "war_support": -0.08, "prestige": -3}, "flavor": "Threat neutralized; loyalty uncertain."},
             {"id": 2, "text": "Increase military pay and privileges. Buy loyalty.", "effects": {"stability": 0.06, "gdp_growth": -0.02, "war_support": 0.04}, "flavor": "Crisis averted at high cost."},
             {"id": 3, "text": "Ignore rumors. Show no weakness.", "effects": {"stability": -0.08, "war_support": -0.04}, "flavor": "The plot advances."},
         ]},
        {"title": "Desertion Crisis",
         "description": "Desertion rates in the military are rising sharply. Morale is at a historic low.",
         "urgency": "high",
         "options": [
             {"id": 1, "text": "Impose harsh penalties for desertion.", "effects": {"war_support": 0.05, "stability": -0.04, "happiness": -0.03}, "flavor": "Discipline imposed; resentment grows."},
             {"id": 2, "text": "Address root causes: better pay and conditions.", "effects": {"war_support": 0.07, "gdp_growth": -0.01, "stability": 0.02}, "flavor": "Morale recovers gradually."},
             {"id": 3, "text": "Increase propaganda and nationalist messaging.", "effects": {"war_support": 0.04, "prestige": -2}, "flavor": "Some motivated; many see through it."},
         ]},
        {"title": "Secret Military Research Program",
         "description": "Scientists propose a classified weapons program. Huge cost, uncertain payoff.",
         "urgency": "normal",
         "options": [
             {"id": 1, "text": "Fund the full black-budget program.", "effects": {"war_support": 0.06, "gdp_growth": -0.02, "research_points": 20}, "flavor": "Breakthrough possible in years."},
             {"id": 2, "text": "Fund joint research with an ally instead.", "effects": {"war_support": 0.03, "prestige": 5, "research_points": 10}, "flavor": "Shared cost; shared gains."},
             {"id": 3, "text": "Reject it. Focus on conventional forces.", "effects": {"war_support": 0.04, "gdp_growth": 0.005}, "flavor": "Practical; scientists frustrated."},
         ]},
        {"title": "Veteran General's Retirement",
         "description": "The nation's most decorated general announces retirement. Succession is disputed.",
         "urgency": "normal",
         "options": [
             {"id": 1, "text": "Appoint the general's chosen successor.", "effects": {"war_support": 0.04, "stability": 0.02}, "flavor": "Smooth transition. Military united."},
             {"id": 2, "text": "Appoint a political loyalist.", "effects": {"stability": 0.04, "war_support": -0.05}, "flavor": "Control secured; officers unhappy."},
             {"id": 3, "text": "Promote from the ranks — a surprise choice.", "effects": {"war_support": 0.02, "prestige": 3, "stability": 0.01}, "flavor": "Fresh blood; eyebrows raised."},
         ]},
    ],
    "diplomatic": [
        {"title": "Territorial Dispute with Neighbor",
         "description": "A neighbor asserts historical claims over a disputed border region.",
         "urgency": "high",
         "options": [
             {"id": 1, "text": "Seek international mediation.", "effects": {"stability": 0.03, "prestige": 5, "war_support": -0.04}, "flavor": "Peace preserved; nationalists feel betrayed."},
             {"id": 2, "text": "Mobilize troops to the border.", "effects": {"war_support": 0.10, "stability": -0.03, "prestige": 3}, "flavor": "Nation rallies; war grows closer."},
             {"id": 3, "text": "Demand binding arbitration through courts.", "effects": {"prestige": 8, "stability": 0.02, "war_support": -0.02}, "flavor": "Slow but peaceful process begins."},
         ]},
        {"title": "Border Smuggling Ring",
         "description": "Smugglers move fuel and weapons across the frontier. State authority is undermined.",
         "urgency": "normal",
         "options": [
             {"id": 1, "text": "Launch a major crackdown operation.", "effects": {"stability": 0.02, "prestige": 3}, "flavor": "Seizures rise; investigations widen."},
             {"id": 2, "text": "Negotiate joint border patrols with neighbor.", "effects": {"prestige": 5, "stability": 0.01}, "flavor": "Cooperation improves relations."},
             {"id": 3, "text": "Tolerate it — other priorities exist.", "effects": {"stability": -0.02, "gdp_growth": 0.005}, "flavor": "Black market expands unchecked."},
         ]},
        {"title": "Foreign Ambassador Expelled",
         "description": "A neighboring state expels your ambassador over alleged espionage activities.",
         "urgency": "high",
         "options": [
             {"id": 1, "text": "Expel their ambassador in retaliation.", "effects": {"prestige": 3, "war_support": 0.04, "stability": -0.02}, "flavor": "Tit-for-tat. Tensions spike."},
             {"id": 2, "text": "Apologize diplomatically. De-escalate.", "effects": {"prestige": -4, "stability": 0.04}, "flavor": "Calm restored; seen as weak."},
             {"id": 3, "text": "Deny everything. Demand their apology.", "effects": {"prestige": 5, "stability": -0.03, "war_support": 0.06}, "flavor": "Bold stance. Dispute deepens."},
         ]},
        {"title": "International Sanctions Threat",
         "description": "A coalition of nations threatens sanctions over your internal policies.",
         "urgency": "high",
         "options": [
             {"id": 1, "text": "Comply with their demands. Avoid sanctions.", "effects": {"stability": 0.03, "prestige": -5, "gdp_growth": 0.01}, "flavor": "Sanctions avoided; sovereignty questioned."},
             {"id": 2, "text": "Defy them. Prepare counter-measures.", "effects": {"war_support": 0.08, "gdp_growth": -0.02, "prestige": 4}, "flavor": "Nationalists cheer; economy hurts."},
             {"id": 3, "text": "Negotiate — partial reform, partial concession.", "effects": {"stability": 0.02, "prestige": 2, "gdp_growth": 0.005}, "flavor": "Crisis defused with compromise."},
         ]},
        {"title": "Treaty of Non-Aggression Proposed",
         "description": "A powerful neighbor proposes a formal non-aggression pact. Advisors are split.",
         "urgency": "normal",
         "options": [
             {"id": 1, "text": "Sign the pact. Reduce border tensions.", "effects": {"stability": 0.05, "war_support": -0.04, "prestige": 4}, "flavor": "Peace secured. Military grumbles."},
             {"id": 2, "text": "Reject it. Maintain strategic flexibility.", "effects": {"war_support": 0.03, "prestige": -3, "stability": -0.02}, "flavor": "Neighbor wary; you stay free."},
             {"id": 3, "text": "Demand better terms before signing.", "effects": {"prestige": 3, "stability": 0.01}, "flavor": "Negotiations drag on."},
         ]},
        {"title": "Disputed Shipping Lane",
         "description": "Your navy and a rival's vessels clash over access to a critical sea trade route.",
         "urgency": "high",
         "options": [
             {"id": 1, "text": "Assert naval sovereignty. Blockade rival ships.", "effects": {"war_support": 0.10, "prestige": 6, "stability": -0.04}, "flavor": "Risky escalation. World watches."},
             {"id": 2, "text": "Negotiate joint use agreement.", "effects": {"prestige": 5, "gdp_growth": 0.01, "stability": 0.02}, "flavor": "Trade flows; dispute deferred."},
             {"id": 3, "text": "Request international arbitration.", "effects": {"prestige": 4, "stability": 0.03, "war_support": -0.03}, "flavor": "Legal route — slow but safe."},
         ]},
    ],
}

_issue_idx: dict[str, int] = {t: 0 for t in _ISSUES}


def _pick_issue_type(player: dict, turn: int) -> str:
    eco        = player.get("economy", {})
    stability  = player.get("stability", 0.70)
    gdp_growth = eco.get("gdp_growth", 0.03)
    unemployed = eco.get("unemployment", 0.08)
    at_war     = player.get("is_at_war", False)

    w = {"economic": 1.0, "political": 1.0, "social": 1.0, "military": 1.0, "diplomatic": 1.0}
    if gdp_growth < 0.0 or unemployed > 0.15:
        w["economic"] += 2.5
    if stability < 0.45:
        w["political"] += 2.2
        w["social"]    += 1.5
    if at_war:
        w["military"]   += 3.0
        w["diplomatic"] += 1.5
    if turn % 5 == 0:
        w["diplomatic"] += 1.5

    total = sum(w.values())
    r = random.uniform(0, total)
    cumul = 0.0
    for itype, wt in w.items():
        cumul += wt
        if r <= cumul:
            return itype
    return "economic"


async def generate_issues(player_nation: dict, turn: int, recent_events: list[str], hint: str = "") -> list[dict]:
    itype = hint if hint in _ISSUES else _pick_issue_type(player_nation, turn)
    pool  = _ISSUES[itype]
    idx   = _issue_idx[itype]
    issue = dict(pool[idx % len(pool)])
    issue["issue_type"] = itype
    _issue_idx[itype] = (idx + 1) % len(pool)
    return [issue]


async def generate_starter_issues(era_name: str, ideology: str, year: int) -> list[dict]:
    issues = []
    for itype, pool in _ISSUES.items():
        issue = dict(random.choice(pool))
        issue["issue_type"] = itype
        issues.append(issue)
    return issues


# ── Diplomatic Responses (delegate to npc_rules) ──────────────────────────────

async def generate_diplomatic_response(target_nation, player_nation, action_type, details) -> dict:
    from backend import npc_rules
    return npc_rules.diplomatic_response(
        target_nation, player_nation, action_type, details,
        world_tension=player_nation.get("world_tension", 0.0),
    )


async def generate_resource_trade_response(target_nation, player_nation, offer_resource, offer_amount, request_resource, request_amount) -> dict:
    from backend import npc_rules
    return npc_rules.resource_trade_response(target_nation, player_nation, offer_amount, request_amount)


async def generate_troop_request_response(target_nation, player_nation, war_id, troops_requested) -> dict:
    from backend import npc_rules
    return npc_rules.troop_request_response(target_nation, player_nation, troops_requested)


async def generate_tech_purchase_response(target_nation, player_nation, tech_branch, price_gdp) -> dict:
    from backend import npc_rules
    return npc_rules.tech_purchase_response(target_nation, player_nation, price_gdp)


async def generate_joint_research_response(target_nation, player_nation, tech_branch) -> dict:
    from backend import npc_rules
    return npc_rules.joint_research_response(target_nation, player_nation)


# ── War Events ────────────────────────────────────────────────────────────────

_WAR_TEMPLATES = {
    "attacker_victory": [
        "{a} Forces Break Through {d} Lines",
        "{a} Army Advances Deep Into {d} Territory",
        "{d} Defenses Collapse — {a} Pushes Forward",
        "Major Offensive: {a} Captures Strategic High Ground",
    ],
    "stalemate": [
        "Fierce Fighting at the Front — Lines Hold",
        "Both Sides Suffer Heavy Losses in Bloody Stalemate",
        "Encirclement Attempt Fails — War of Attrition Continues",
        "Strategic Reserve Deployed — Battle Hangs in Balance",
    ],
    "defender_victory": [
        "{d} Repels Major {a} Offensive",
        "{a} Assault Stalls — {d} Counterattacks",
        "{d} Fortifications Hold Against All Assaults",
        "{a} Forces Retreat After Costly Failed Offensive",
    ],
}

_WAR_DESCRIPTIONS = {
    "attacker_victory": "{a} forces pushed forward successfully, capturing ground and inflicting heavy casualties.",
    "stalemate": "Neither side could achieve a decisive breakthrough. The front lines hold steady after brutal fighting.",
    "defender_victory": "{d} repelled the assault, forcing {a} units to fall back with significant losses.",
}


async def generate_war_events(attacker: dict, defender: dict, war: dict) -> dict:
    """Military simulation — instant, no network."""
    a_army   = attacker.get("military", {}).get("army_size", 100_000)
    d_army   = defender.get("military", {}).get("army_size", 100_000)
    a_equip  = attacker.get("military", {}).get("equipment_level", 0.70)
    d_equip  = defender.get("military", {}).get("equipment_level", 0.70)
    a_morale = attacker.get("military", {}).get("morale", 0.75)
    d_morale = defender.get("military", {}).get("morale", 0.75)

    # Attacker gets a 5% initiative bonus
    a_score = a_army * a_equip * a_morale * random.uniform(0.86, 1.14) * 1.05
    d_score = d_army * d_equip * d_morale * random.uniform(0.86, 1.14)
    ratio   = a_score / max(1, d_score)

    if ratio > 1.25:
        result = "attacker_victory"
        ws_change  = random.randint(4,  9)
        a_losses   = int(a_army * random.uniform(0.02, 0.05))
        d_losses   = int(d_army * random.uniform(0.06, 0.13))
    elif ratio > 0.82:
        result = "stalemate"
        ws_change  = random.randint(-2, 2)
        a_losses   = int(a_army * random.uniform(0.03, 0.07))
        d_losses   = int(d_army * random.uniform(0.03, 0.07))
    else:
        result = "defender_victory"
        ws_change  = random.randint(-9, -3)
        a_losses   = int(a_army * random.uniform(0.06, 0.13))
        d_losses   = int(d_army * random.uniform(0.02, 0.05))

    aname = attacker.get("name", "Attacker")
    dname = defender.get("name", "Defender")
    headline = random.choice(_WAR_TEMPLATES[result]).format(a=aname, d=dname)
    desc     = _WAR_DESCRIPTIONS[result].format(a=aname, d=dname)

    return {
        "battle_result":    result,
        "warscore_change":  ws_change,
        "attacker_losses":  a_losses,
        "defender_losses":  d_losses,
        "headline":         headline,
        "event_description": desc,
    }


# ── Peace Terms ───────────────────────────────────────────────────────────────

async def generate_peace_terms(winner: dict, loser: dict, warscore: float) -> dict:
    ln = loser.get("name", "the enemy")
    return {
        "available_terms": [
            {"id": "annex",        "label": "Full Annexation",           "description": f"Completely absorb {ln}.",                    "cost_warscore": 100, "effects": {"prestige": 20}},
            {"id": "puppet",       "label": "Install Puppet Government", "description": f"Install a loyal regime in {ln}.",            "cost_warscore":  60, "effects": {"prestige": 10}},
            {"id": "reparations",  "label": "Demand Reparations",        "description": "Extract war payments and resources.",          "cost_warscore":  30, "effects": {"gdp_change": 20, "prestige": 5}},
            {"id": "demilitarize", "label": "Demilitarization Treaty",   "description": f"Force {ln} to drastically reduce military.", "cost_warscore":  25, "effects": {"prestige": 8}},
            {"id": "status_quo",   "label": "White Peace",               "description": "Return to pre-war borders. No gains.",        "cost_warscore":   0, "effects": {"prestige": -5}},
        ],
        "flavor_text": f"{ln} awaits your judgement.",
    }


# ── News Headlines ────────────────────────────────────────────────────────────

_NEWS_TEMPLATES: dict[str, list[str]] = {
    "war_declared":    ["{attacker} Declares War on {defender}", "{attacker} Launches Offensive Against {defender}", "War Erupts: {attacker} Attacks {defender}"],
    "alliance_formed": ["{nation1} and {nation2} Sign Historic Alliance Pact", "New Military Partnership: {nation1}–{nation2}", "Mutual Defense Treaty Reshapes Regional Balance"],
    "peace_signed":    ["Peace Treaty Ends {nation1}–{nation2} Conflict", "{nation1} and {nation2} Agree to Ceasefire", "War Ends: Armistice Signed"],
    "sanctions":       ["Economic Sanctions Imposed on {target}", "{nation} Targets {target} With Trade Restrictions", "Trade War Erupts Over Policy Dispute"],
    "tension_high":    ["World Leaders Warn of Impending Crisis", "Arms Race Intensifies as Tension Reaches Breaking Point", "UN Emergency Session Called as War Looms"],
    "economic":        ["Global Markets Rally on Positive Growth Data", "Trade Routes Expand as Nations Sign Deals", "Industrial Output Hits Record Highs"],
    "diplomacy":       ["Historic Diplomatic Summit Draws World Leaders", "New Trade Corridor Opens Between Nations", "Ambassador Exchange Signals Thaw in Relations"],
}


async def generate_news_headline(event_type: str, context: dict) -> str:
    templates = _NEWS_TEMPLATES.get(event_type, _NEWS_TEMPLATES["diplomacy"])
    tpl = random.choice(templates)
    return tpl.format(
        attacker=context.get("attacker", "Unknown Nation"),
        defender=context.get("defender", "Unknown Nation"),
        nation1=context.get("nation1", context.get("attacker", "Unknown")),
        nation2=context.get("nation2", context.get("defender", "Unknown")),
        nation=context.get("nation", context.get("attacker", "Unknown")),
        target=context.get("target", context.get("defender", "Unknown")),
    )


async def generate_starter_news(era_name: str, player_nation: str, year: int) -> list[str]:
    return [
        f"World Leaders Gather for {era_name} Summit in {year}",
        "Economic Growth Continues Amid Global Uncertainty",
        "Military Modernization Programs Accelerate Worldwide",
        "Diplomatic Tensions Rise Over Disputed Territories",
        "New Trade Routes Open Between Eastern and Western Nations",
        "Scientists Announce Major Industrial Breakthrough",
        "Refugee Crisis Strains International Aid Networks",
        "Naval Powers Contest Control of Strategic Waterways",
    ]
