"""
Pre-written issue library — NationStates style.
Vivid character voices, satirical situations, stat-based conditions, chained issues.
"""
import random
from typing import Optional


# ── Issue library ─────────────────────────────────────────────────────────────
#
# Fields:
#   id            — unique string
#   title         — headline
#   description   — newspaper-style opening paragraph
#   issue_type    — economic / political / social / military / diplomatic
#   urgency       — low / normal / high / critical
#   era_years     — list of (start, end) tuples
#   ideology_tags — [] = all ideologies; or list of specific ones
#   conditions    — optional dict of stat thresholds:
#                   min_stability, max_stability, min_unemployment, max_unemployment,
#                   min_world_tension, max_world_tension, at_war (bool),
#                   min_happiness, max_happiness, min_gdp_growth, max_gdp_growth
#   chains_from   — optional {issue_id: str, option_id: int}
#                   issue only appears after player chose that option in that issue
#   advisors      — list of {name, role, icon, option_id, quote}
#   options       — list of {id, text, effects, flavor, news}

ISSUES = [

    # ════════════════════════════════════════════════════════════
    #  UNIVERSAL — General issues, all eras
    # ════════════════════════════════════════════════════════════

    {
        "id": "u_rap_trial",
        "title": "Musician's Hit Song Contains Possible Confession",
        "description": (
            "Notorious gangster-rapper Wally Eigendorf was recently acquitted of "
            "murdering a policeman due to lack of evidence — which surprised many, "
            "as his most popular song, 'I Killed A Cop And I Liked It', "
            "contained what prosecutors call a 'fairly detailed and enthusiastic "
            "account' of the shooting. The trial has divided the nation between "
            "those who believe artistic expression must be protected at all costs, "
            "and those who believe Eigendorf simply got away with murder."
        ),
        "issue_type": "social",
        "urgency": "normal",
        "era_years": [(1900, 2060)],
        "ideology_tags": [],
        "conditions": {},
        "advisors": [
            {
                "name": "Elizabeth Jobrani",
                "role": "Right-Wing Commentator",
                "icon": "📢",
                "option_id": 1,
                "quote": (
                    "How could we let this happen? Rap music is just sick minds preaching "
                    "to a sick audience. We're talking about a recorded confession, flaunted "
                    "in public. Rappers should be held to account for their hateful words, "
                    "and their filth music should be admissible in court. I say: lock him up."
                ),
            },
            {
                "name": "Wally Eigendorf",
                "role": "Acquitted Rapper",
                "icon": "🎤",
                "option_id": 2,
                "quote": (
                    "Woah woah woah, I mean... just 'cos I got, you know, artistic words "
                    "doesn't mean you haters should hate me. I don't mean everything in my "
                    "songs literally. We should be free to, like, artistically express. "
                    "We are artists. Expressing ourselves. So don't hate on me. Yeah."
                ),
            },
            {
                "name": "Jonas Pfeiffer-Quinn",
                "role": "Classical Guitarist & Cultural Commentator",
                "icon": "🎸",
                "option_id": 3,
                "quote": (
                    "The problem here is that this genre of music is terrible trash, "
                    "enjoyed only by the musically illiterate. The government should create "
                    "an official Culture Standards Bureau to regulate what sort of material "
                    "gets airplay. Frankly, we need a better class of art, full stop."
                ),
            },
        ],
        "options": [
            {
                "id": 1,
                "text": "Make artistic works admissible as court evidence",
                "effects": {"stability": -0.03, "prestige": -4, "war_support": 0.02},
                "flavor": "Wally Eigendorf is retried and convicted. His album sales double overnight.",
                "news": "Court Ruling: Song Lyrics Now Admissible as Legal Evidence",
            },
            {
                "id": 2,
                "text": "Uphold artistic freedom; lyrics are protected expression",
                "effects": {"stability": 0.03, "prestige": 5, "happiness": 0.02},
                "flavor": "Wally releases a follow-up album entitled 'Still Innocent'. It also goes platinum.",
                "news": "Government Defends Artistic Freedom — Acquittal Upheld",
            },
            {
                "id": 3,
                "text": "Establish a national Culture Standards Bureau",
                "effects": {"stability": -0.04, "prestige": -6, "happiness": -0.03},
                "flavor": "Underground music scenes immediately explode in popularity. Wally goes on tour.",
                "news": "New Cultural Censorship Bureau Sparks Underground Arts Movement",
            },
        ],
    },

    {
        "id": "u_street_food",
        "title": "Street Vendors vs. The Health Inspector",
        "description": (
            "Street food vendor Magdalena Voss has been selling her famous spiced "
            "meat pies from a cart outside the parliament building for twenty-three years. "
            "Health Inspector Reginald Dunmore has just condemned her cart as a "
            "'biological hazard' after finding what he describes as 'a small ecosystem "
            "living inside the gravy pot'. Magdalena's supporters — a loud coalition "
            "of office workers, politicians, and at least one judge — insist "
            "the pies have never once made anyone seriously ill. The Inspector is "
            "threatening to confiscate the cart by Friday."
        ),
        "issue_type": "economic",
        "urgency": "low",
        "era_years": [(1815, 2060)],
        "ideology_tags": [],
        "conditions": {},
        "advisors": [
            {
                "name": "Inspector Reginald Dunmore",
                "role": "Chief Health Inspector",
                "icon": "🔬",
                "option_id": 1,
                "quote": (
                    "There are THINGS in that gravy, Minister. Living things. I have photographs. "
                    "We cannot allow unregulated food preparation to operate in the shadow "
                    "of our parliament. Licence her properly, make her use a certified kitchen, "
                    "and if she refuses — confiscate the cart. Hygiene is not negotiable."
                ),
            },
            {
                "name": "Magdalena Voss",
                "role": "Street Food Vendor, 23 Years",
                "icon": "🥧",
                "option_id": 2,
                "quote": (
                    "Twenty-three years! TWENTY-THREE. Not a single complaint. Your own "
                    "Justice Minister eats here every Wednesday. The chief of police takes "
                    "two pies every Friday. Dunmore has it out for me because I once refused "
                    "to give him a free one. Leave my cart alone and leave the working people alone."
                ),
            },
            {
                "name": "CEO of NourishChain Group",
                "role": "Fast Food Multinational Executive",
                "icon": "🍔",
                "option_id": 3,
                "quote": (
                    "Look, I'm not saying we got Dunmore his job. But I am saying that "
                    "NourishChain has sixteen certified, regularly-inspected, standardised "
                    "restaurants within walking distance of parliament. We create jobs. "
                    "We pay taxes. We don't have ecosystems in our gravy. Just sayin'."
                ),
            },
        ],
        "options": [
            {
                "id": 1,
                "text": "Enforce food safety codes; require licencing for all street vendors",
                "effects": {"stability": -0.02, "gdp_growth": -0.003, "happiness": -0.02},
                "flavor": "Magdalena closes her cart. Seventy MPs skip lunch in protest.",
                "news": "Health Crackdown: Street Food Vendors Must Now Be Licenced",
            },
            {
                "id": 2,
                "text": "Dismiss the complaint; let Magdalena keep her cart",
                "effects": {"stability": 0.02, "happiness": 0.03, "prestige": -2},
                "flavor": "Magdalena celebrates with free pies for the entire parliamentary press corps. "
                          "Inspector Dunmore submits a strongly worded letter.",
                "news": "Government Overrules Health Inspector — Beloved Pie Cart Stays",
            },
            {
                "id": 3,
                "text": "Grant tax breaks to certified fast food chains to 'modernise' food culture",
                "effects": {"gdp_growth": 0.005, "happiness": -0.03, "prestige": -5},
                "flavor": "A NourishChain opens where Magdalena's cart used to be. Nobody is happy.",
                "news": "Government Tax Break Sees Chain Restaurants Displace Street Vendors",
            },
        ],
    },

    {
        "id": "u_census_nightmare",
        "title": "The Census Has Gone Slightly Wrong",
        "description": (
            "The results of the national census are in, and statistician Dr. Ilona Faversham "
            "has emerged from the archives looking like she has seen things. "
            "Apparently one in eight citizens listed their occupation as 'vibes'. "
            "Twelve thousand people claim to be 'professionally retired' despite being "
            "under thirty. And an entire village in the northern province has, collectively, "
            "declared their religion to be 'the concept of cheese'. "
            "The data is, according to Dr. Faversham, 'technically valid but spiritually concerning'."
        ),
        "issue_type": "political",
        "urgency": "low",
        "era_years": [(1815, 2060)],
        "ideology_tags": [],
        "conditions": {},
        "advisors": [
            {
                "name": "Dr. Ilona Faversham",
                "role": "Director of National Statistics",
                "icon": "📊",
                "option_id": 1,
                "quote": (
                    "These forms are legally binding government documents and must be accurate. "
                    "I am recommending we re-run the census with clearer mandatory fields, "
                    "and prosecute anyone who deliberately files nonsense data. "
                    "'Vibes' is not a taxable occupation category. This affects our entire "
                    "planning infrastructure."
                ),
            },
            {
                "name": "Alderman Clive Brockett",
                "role": "Mayor of the Cheese Village",
                "icon": "🧀",
                "option_id": 2,
                "quote": (
                    "With respect, Doctor, we answered honestly. Cheese has guided us "
                    "through hard winters for generations. Our ancestors did not flee "
                    "persecution so that some statistician in the capital could tell us "
                    "our spiritual beliefs aren't real. Leave us alone. "
                    "Also our cheese is excellent if you'd like some."
                ),
            },
            {
                "name": "Revenue Minister Pavel Obrecht",
                "role": "Ministry of Taxation",
                "icon": "💸",
                "option_id": 3,
                "quote": (
                    "I actually see an opportunity here. If 'vibes' is an occupation, "
                    "vibes can be taxed. If cheese is a religion, churches can be "
                    "subject to the standard religious institution transparency requirements. "
                    "We just need to formalise what these people are claiming and the "
                    "revenue possibilities become rather interesting."
                ),
            },
        ],
        "options": [
            {
                "id": 1,
                "text": "Re-run the census with strict mandatory fields; prosecute fraudulent entries",
                "effects": {"stability": -0.02, "prestige": 3, "happiness": -0.03},
                "flavor": "The second census is slightly more accurate and significantly less interesting.",
                "news": "Government Orders Re-Run of 'Deeply Weird' National Census",
            },
            {
                "id": 2,
                "text": "Accept the data as submitted — citizens know themselves best",
                "effects": {"stability": 0.02, "happiness": 0.04, "prestige": -3},
                "flavor": "Policy planning becomes extremely creative. The cheese village sends a gift basket.",
                "news": "Census Accepted: Nation Officially Has 12,000 Under-30 Retirees",
            },
            {
                "id": 3,
                "text": "Create new official tax categories for unconventional occupations and beliefs",
                "effects": {"gdp_growth": 0.006, "stability": -0.01, "happiness": -0.02},
                "flavor": "The 'vibes tax' raises a modest but philosophically fascinating revenue stream.",
                "news": "New Tax Categories: 'Vibes', 'Cheese Theology' Now Officially Recognised",
            },
        ],
    },

    {
        "id": "u_prison_crisis",
        "title": "The Prisons Are Full — Of Newsletters",
        "description": (
            "The National Prison Service has issued an embarrassing report: "
            "the nation's jails are at 148% capacity. Warden Horst Klemm of "
            "Greystone Correctional reports that inmates are 'hot-bunking', "
            "sharing cells designed for two between seven, and have taken to "
            "publishing a remarkably well-edited inmate newspaper, 'The Greystone Gazette', "
            "which has a better proofreading record than the national broadsheet. "
            "Something must be done about the overcrowding. "
            "The Gazette's editorial board has opinions."
        ),
        "issue_type": "political",
        "urgency": "high",
        "era_years": [(1815, 2060)],
        "ideology_tags": [],
        "conditions": {},
        "advisors": [
            {
                "name": "Warden Horst Klemm",
                "role": "Greystone Correctional Facility",
                "icon": "🔑",
                "option_id": 1,
                "quote": (
                    "Build more prisons. Simple. I've been saying it for six years. "
                    "We're legally obligated to house these people, Minister. "
                    "Instead I've got inmates sleeping in shifts and a newspaper staff "
                    "that has better office hours than my actual staff. "
                    "Give me more cells or give me less prisoners. Either. Both. Please."
                ),
            },
            {
                "name": "Judge Priya Osei-Bonsu",
                "role": "Chief Justice, Criminal Reform Bench",
                "icon": "⚖️",
                "option_id": 2,
                "quote": (
                    "Sixty percent of the people in Warden Klemm's facility are "
                    "serving sentences under six months for non-violent offences. "
                    "Community service, fines, electronic monitoring — all cheaper "
                    "and more effective at rehabilitation than stacking humans in a "
                    "box. Build smarter sentencing, not bigger boxes."
                ),
            },
            {
                "name": "The Greystone Gazette Editorial Board",
                "role": "Inmate Newspaper",
                "icon": "📰",
                "option_id": 3,
                "quote": (
                    "The Gazette respectfully submits that the root cause of recidivism "
                    "is lack of education and economic opportunity post-release. "
                    "We've run three feature investigations on this. We'd send you "
                    "copies but apparently our subscription requests to government "
                    "departments keep getting lost. Invest in rehabilitation programmes. "
                    "We'd appreciate a reply."
                ),
            },
        ],
        "options": [
            {
                "id": 1,
                "text": "Fund construction of three new large prisons",
                "effects": {"stability": 0.02, "gdp_growth": -0.010, "war_support": 0.02},
                "flavor": "The new facilities open. They are full within eighteen months.",
                "news": "Three New Prisons Approved — Critics Ask 'Why Are There So Many Criminals?'",
            },
            {
                "id": 2,
                "text": "Reform sentencing — community service for non-violent offenders",
                "effects": {"stability": 0.04, "happiness": 0.03, "gdp_growth": -0.003},
                "flavor": "Occupancy drops to 90%. Judge Osei-Bonsu calls it 'a start'.",
                "news": "Sentencing Reform Cuts Prison Population — Non-Violent Offenders Released",
            },
            {
                "id": 3,
                "text": "Invest in education and job placement programmes for inmates",
                "effects": {"stability": 0.05, "happiness": 0.04, "unemployment": -0.01, "gdp_growth": -0.007},
                "flavor": "Three years later, the Gazette wins a national journalism award. "
                          "Reoffending rates drop 20%.",
                "news": "Prison Rehabilitation Investment Bears Fruit — Reoffending Rates Fall",
            },
        ],
    },

    {
        "id": "u_royal_pet",
        "title": "The State Animal Has Escaped Again",
        "description": (
            "Archibald, the nation's officially designated state animal — "
            "a large and unusually opinionated cassowary gifted by a foreign head of state "
            "fourteen years ago — has escaped from the zoological gardens for the fifth time "
            "this year. He has been spotted in three different government ministries, "
            "eaten a considerable number of official documents, and cornered the Deputy "
            "Finance Minister in a broom cupboard for forty-five minutes. "
            "The zoological director says he simply cannot be contained. "
            "Parliament is demanding action."
        ),
        "issue_type": "political",
        "urgency": "low",
        "era_years": [(1815, 2060)],
        "ideology_tags": [],
        "conditions": {},
        "advisors": [
            {
                "name": "Director Helmut Saupe",
                "role": "National Zoological Gardens",
                "icon": "🦜",
                "option_id": 1,
                "quote": (
                    "Cassowaries are, frankly, nearly impossible to contain without "
                    "purpose-built maximum-security enclosures. This will cost money. "
                    "A lot of money. But the alternative is Archibald continuing to "
                    "eat ministerial briefings and headbutt civil servants. "
                    "I leave the cost-benefit analysis to you."
                ),
            },
            {
                "name": "Deputy Finance Minister Oswald Pring",
                "role": "The Broom Cupboard Incident Survivor",
                "icon": "😰",
                "option_id": 2,
                "quote": (
                    "I was in there for FORTY-FIVE MINUTES. He just stared at me. "
                    "Unblinking. I want Archibald returned to the country that sent him. "
                    "Diplomatic gift or not, this bird is a menace and I have the "
                    "scratches to prove it. Send him home."
                ),
            },
            {
                "name": "Countess Emilia von Strutz",
                "role": "National Tourism Board",
                "icon": "🏛️",
                "option_id": 3,
                "quote": (
                    "Do you know how many visitors come specifically to see Archibald? "
                    "His last escape generated more press coverage than the budget. "
                    "Lean into it. A 'Wild Archibald Tour'. Merchandise. We turn the "
                    "chaos into a national character moment. I've drafted a marketing "
                    "plan. It involves a commemorative broom cupboard."
                ),
            },
        ],
        "options": [
            {
                "id": 1,
                "text": "Fund a proper maximum-security cassowary enclosure",
                "effects": {"gdp_growth": -0.002, "stability": 0.01, "prestige": 2},
                "flavor": "Archibald escapes twice more during construction, then appears to give up.",
                "news": "Government Builds Fortified Cassowary Enclosure for Repeat-Offender State Bird",
            },
            {
                "id": 2,
                "text": "Return Archibald diplomatically to his country of origin",
                "effects": {"stability": 0.02, "prestige": -4, "happiness": -0.01},
                "flavor": "The sending nation is offended. Archibald, reportedly, does not care.",
                "news": "State Cassowary Deported — Diplomatic Row Ensues",
            },
            {
                "id": 3,
                "text": "Embrace Archibald as a national icon; launch tourism campaign",
                "effects": {"prestige": 6, "gdp_growth": 0.004, "happiness": 0.03},
                "flavor": "Archibald becomes the most photographed living thing in the country. "
                          "He escapes twice more. Nobody minds.",
                "news": "Escaped State Cassowary Becomes Unlikely Tourism Sensation",
            },
        ],
    },

    {
        "id": "u_propaganda_art",
        "title": "Government-Commissioned Mural Is... Something",
        "description": (
            "The newly unveiled mural in the Grand Hall of the People — commissioned "
            "at a cost of 400,000 units from avant-garde artist Bernadette Scholl — "
            "has sparked a national controversy. Critics call it 'a masterpiece of "
            "uncomfortable truth'. Members of the public call it 'very upsetting'. "
            "The mural depicts the leader of the nation as a confused-looking badger "
            "surrounded by burning money. The artist insists it is 'a meditation on "
            "the soul of governance'. The press is having an extraordinary week."
        ),
        "issue_type": "political",
        "urgency": "low",
        "era_years": [(1815, 2060)],
        "ideology_tags": [],
        "conditions": {},
        "advisors": [
            {
                "name": "Bernadette Scholl",
                "role": "Avant-Garde Artist, Contract Holder",
                "icon": "🎨",
                "option_id": 1,
                "quote": (
                    "Art is supposed to make you uncomfortable. If the government wanted "
                    "a flattering portrait, they should have commissioned a photographer. "
                    "I delivered exactly what my artistic vision required. The badger "
                    "represents institutional uncertainty. The burning money is hope. "
                    "This is quite clearly stated in my artist's statement, which I "
                    "provided at the time."
                ),
            },
            {
                "name": "Press Secretary Alaric Nance",
                "role": "Government Communications",
                "icon": "📣",
                "option_id": 2,
                "quote": (
                    "We need to get ahead of this. The story is currently 'Leader Badger'. "
                    "In twenty-four hours it will be 'Leader Badger, Continued'. "
                    "Commission a replacement — something with eagles and sunrises and "
                    "historical gravitas — and quietly retire Ms. Scholl's contribution "
                    "to a storage facility in the provinces. Crisis managed."
                ),
            },
            {
                "name": "Tourism Director Countess von Strutz",
                "role": "National Tourism Board",
                "icon": "🏛️",
                "option_id": 3,
                "quote": (
                    "We have had twelve thousand visitors to the Grand Hall this week alone. "
                    "I don't know what a confused badger means but it is absolutely "
                    "driving ticket sales. Leave it exactly where it is. "
                    "I'm already developing a 'Badger Hall' gift range."
                ),
            },
        ],
        "options": [
            {
                "id": 1,
                "text": "Defend the mural as protected artistic expression; leave it up",
                "effects": {"prestige": 4, "happiness": 0.02, "stability": -0.01},
                "flavor": "The mural becomes a pilgrimage site for art students. "
                          "The badger gets its own commemorative stamp.",
                "news": "Government Backs Controversial Badger Mural as 'Important Art'",
            },
            {
                "id": 2,
                "text": "Have the mural quietly removed and replaced with something dignified",
                "effects": {"prestige": -3, "happiness": -0.02, "stability": 0.01},
                "flavor": "The mural is removed at 3am. Someone photographs the removal. "
                          "The photo goes more viral than the mural did.",
                "news": "Controversial Government Mural Removed Under Cover of Darkness",
            },
            {
                "id": 3,
                "text": "Lean into it — make the badger an official tourism attraction",
                "effects": {"prestige": 6, "gdp_growth": 0.003, "happiness": 0.04},
                "flavor": "The Badger Hall gift shop is the most profitable square metre in the country.",
                "news": "Badger Mural Declared National Treasure — Tourism Revenue Soars",
            },
        ],
    },

    {
        "id": "u_traffic_disaster",
        "title": "The Great Traffic Jam of Our Times",
        "description": (
            "The nation's capital has, according to transportation researcher "
            "Dr. Agneta Viklund, achieved the remarkable distinction of having "
            "the worst traffic congestion in the known world. "
            "Her study found that the average commute takes four hours and eleven minutes, "
            "that three separate couples have reportedly met, fallen in love, "
            "married, and divorced in the same traffic queue, and that one man, "
            "Thomas Brewster, has been technically commuting for eleven months. "
            "He now works from his car. He is doing fine."
        ),
        "issue_type": "economic",
        "urgency": "normal",
        "era_years": [(1900, 2060)],
        "ideology_tags": [],
        "conditions": {},
        "advisors": [
            {
                "name": "Thomas Brewster",
                "role": "Professional Commuter, Month 11",
                "icon": "🚗",
                "option_id": 1,
                "quote": (
                    "I want a train. I just want a train. I have not seen my house since February. "
                    "My children have stopped calling. My potted plant is dead. "
                    "I'm not asking for anything extravagant. Just a train. "
                    "One train. Going roughly the right direction. "
                    "Please."
                ),
            },
            {
                "name": "Motorway Consortium of Businessmen",
                "role": "Road Infrastructure Lobby",
                "icon": "🏗️",
                "option_id": 2,
                "quote": (
                    "The answer is simple: more roads. Wider roads. Faster roads. "
                    "The data is clear — every time you add road capacity, traffic flows better. "
                    "We've prepared eighteen studies. Coincidentally, our members build roads. "
                    "But the studies are completely independent. Completely."
                ),
            },
            {
                "name": "Dr. Agneta Viklund",
                "role": "Transportation Research Institute",
                "icon": "🚉",
                "option_id": 3,
                "quote": (
                    "Adding roads doesn't reduce traffic — it induces more driving. "
                    "Every city that solved congestion did it with public transport "
                    "and congestion charging, not motorways. Invest in rail, bus, cycle "
                    "infrastructure, and charge drivers to enter the city centre. "
                    "The evidence is overwhelming and has been for sixty years."
                ),
            },
        ],
        "options": [
            {
                "id": 1,
                "text": "Build a mass rapid transit railway network",
                "effects": {"gdp_growth": -0.012, "happiness": 0.06, "stability": 0.03, "unemployment": -0.01},
                "flavor": "Thomas Brewster takes the train on its first day of operation. "
                          "He cries. It takes twenty minutes.",
                "news": "Metro Rail Network Opens — City Commuters Report 'Unprecedented Feelings of Hope'",
            },
            {
                "id": 2,
                "text": "Expand the motorway network",
                "effects": {"gdp_growth": -0.008, "happiness": -0.01, "stability": 0.01},
                "flavor": "The new roads fill with cars within six months. Thomas Brewster's commute "
                          "is now four hours and twenty minutes.",
                "news": "New Motorway Expansion Complete — Traffic Experts Call It 'Predictably Pointless'",
            },
            {
                "id": 3,
                "text": "Congestion charges plus major public transport investment",
                "effects": {"gdp_growth": -0.010, "happiness": 0.04, "stability": 0.02, "prestige": 4},
                "flavor": "Congestion drops 40%. Motorists complain for three years, then get the train.",
                "news": "Congestion Charging Scheme Introduced — Public Transport Investment Follows",
            },
        ],
    },

    {
        "id": "u_healthcare_birth",
        "title": "Mother Dies Because the Bill Was Too High",
        "description": (
            "An investigative journalist named Ifeoma Achebe has published a devastating "
            "account: a young mother named Amara Diallo died during childbirth "
            "because her family could not afford the cost of an emergency caesarean. "
            "The story has consumed the national conversation for a week. "
            "A government spokesman initially called it 'an isolated incident', "
            "which was a poor choice of words given that Dr. Vasquez's hospital "
            "records show seventeen similar cases in the past two years."
        ),
        "issue_type": "social",
        "urgency": "high",
        "era_years": [(1815, 2060)],
        "ideology_tags": [],
        "conditions": {},
        "advisors": [
            {
                "name": "Dr. Elena Vasquez",
                "role": "Chief of Obstetrics, Central Hospital",
                "icon": "🏥",
                "option_id": 1,
                "quote": (
                    "Seventeen cases in two years. Seventeen. I have the files. "
                    "I submitted them to the ministry last year and received a form letter "
                    "in return. This is not an isolated incident — it is a policy. "
                    "A policy that kills mothers. Universal coverage. Now. "
                    "Not a study, not a pilot programme, not a consultation. Now."
                ),
            },
            {
                "name": "Viktor Hargreaves",
                "role": "CEO, National Pharmaceutical Consortium",
                "icon": "💊",
                "option_id": 2,
                "quote": (
                    "I understand the tragedy, and my heart goes out to the family. "
                    "But the solution isn't state takeover of medicine. That creates "
                    "waiting lists, rationing, and bureaucratic waste. Targeted subsidies "
                    "for the poorest families — means-tested, carefully managed — "
                    "provide support without destroying the market that funds "
                    "medical innovation. Think about the long term."
                ),
            },
            {
                "name": "Karl Baumann",
                "role": "Chairman, United Healthcare Workers' Union",
                "icon": "✊",
                "option_id": 3,
                "quote": (
                    "Hargreaves just said a woman died and his first thought was 'market'. "
                    "Let me be clear about what happened here: we decided money was "
                    "more important than a mother's life, and the mother died. "
                    "Nationalise it. Run it as a public service. Tax the Hargreaves of the "
                    "world to pay for it. This is not complicated."
                ),
            },
        ],
        "options": [
            {
                "id": 1,
                "text": "Establish universal free public healthcare for all citizens",
                "effects": {"stability": 0.07, "happiness": 0.09, "gdp_growth": -0.014},
                "flavor": "The programme launches. Dr. Vasquez's files stop growing.",
                "news": "Universal Healthcare Passes — 'No One Should Die Over a Bill', Says Minister",
            },
            {
                "id": 2,
                "text": "Means-tested subsidies for low-income families",
                "effects": {"stability": 0.02, "happiness": 0.03, "gdp_growth": -0.004},
                "flavor": "The bureaucratic application process turns away 40% of eligible families. "
                          "Dr. Vasquez submits another file.",
                "news": "Government Launches Healthcare Subsidy — Critics Say It Falls Short",
            },
            {
                "id": 3,
                "text": "Nationalise hospitals; treat healthcare as a public utility",
                "effects": {"stability": -0.02, "happiness": 0.07, "gdp_growth": -0.018, "prestige": -3},
                "flavor": "Business associations threaten to pull investment. "
                          "Approval ratings hit a fifteen-year high.",
                "news": "Mass Nationalisation of Hospitals Announced — Business Lobby Furious",
            },
        ],
    },

    {
        "id": "u_press_freedom",
        "title": "The Paper That Knew Too Much",
        "description": (
            "The venerable newspaper 'The Morning Chronicle' has published a "
            "seven-part investigative series, written by journalist Irena Popescu, "
            "revealing that three cabinet ministers have been accepting payments "
            "from a foreign mining consortium in exchange for favourable contracts. "
            "Popescu received the documents from an anonymous source and refuses "
            "to name them. The Justice Minister is calling the series 'treasonous'. "
            "Popescu is calling the Justice Minister 'one of the three ministers'."
        ),
        "issue_type": "political",
        "urgency": "high",
        "era_years": [(1815, 2060)],
        "ideology_tags": [],
        "conditions": {},
        "advisors": [
            {
                "name": "Justice Minister Aldric Novak",
                "role": "Ministry of Justice",
                "icon": "⚖️",
                "option_id": 1,
                "quote": (
                    "The documents were obtained illegally. The publication was reckless. "
                    "And frankly — and I cannot stress this enough — I am absolutely "
                    "not one of the three ministers. That is a defamatory allegation and "
                    "I will be suing. Separately, the paper should be shut down immediately "
                    "for national security reasons. Unrelated reasons. Completely unrelated."
                ),
            },
            {
                "name": "Irena Popescu",
                "role": "Investigative Journalist, The Morning Chronicle",
                "icon": "📰",
                "option_id": 2,
                "quote": (
                    "I have receipts. I have bank records. I have emails. I have a photograph "
                    "of Minister Novak at a dinner with the consortium CEO that he later "
                    "told parliament he had 'never attended'. "
                    "If the government shuts this paper down, I will publish everything "
                    "I have left on the front page first. Press freedom is not negotiable."
                ),
            },
            {
                "name": "Attorney-General Mina Hoang",
                "role": "Office of the Attorney General",
                "icon": "🏛️",
                "option_id": 3,
                "quote": (
                    "This is exactly what independent judicial oversight exists for. "
                    "Refer the matter to a standing committee. "
                    "The investigation runs independently of ministerial influence. "
                    "The paper continues to publish. Justice takes its course. "
                    "Minister Novak can make his case through proper legal channels "
                    "like everyone else."
                ),
            },
        ],
        "options": [
            {
                "id": 1,
                "text": "Shut down the newspaper; prosecute Popescu for obtaining leaked documents",
                "effects": {"stability": -0.09, "prestige": -14, "happiness": -0.05},
                "flavor": "The Chronicle's final edition before closure sells more copies "
                          "than any edition in its history. Popescu continues writing online.",
                "news": "Government Shuts Newspaper — Journalist Vows to Keep Publishing",
            },
            {
                "id": 2,
                "text": "Guarantee press freedom; launch full corruption inquiry",
                "effects": {"stability": 0.07, "prestige": 12, "happiness": 0.05},
                "flavor": "All three ministers resign within a week. "
                          "Novak is found to have attended 'the dinner he never attended'.",
                "news": "Full Corruption Inquiry Launched — Three Ministers Resign",
            },
            {
                "id": 3,
                "text": "Refer to independent parliamentary committee; paper continues",
                "effects": {"stability": 0.04, "prestige": 5, "happiness": 0.02},
                "flavor": "The committee reports in four months. "
                          "The findings confirm what Popescu wrote. Novak calls it 'biased'.",
                "news": "Parliamentary Committee to Probe Corruption Allegations — Press Continues",
            },
        ],
    },

    {
        "id": "u_labour_strike",
        "title": "The Factories Have Gone Silent",
        "description": (
            "Forty-two thousand factory workers have walked off the job across the "
            "industrial belt. Their leader, a former machinist named Tomasz Wierzbicki, "
            "arrived at the Ministry of Labour this morning in work boots, "
            "presented a list of demands written on the back of a production schedule, "
            "and told the Deputy Secretary — politely but with some force — "
            "that the workers would return when they had an answer "
            "and not a moment before. The Deputy Secretary has been trying "
            "to reach someone in Cabinet for six hours."
        ),
        "issue_type": "economic",
        "urgency": "high",
        "era_years": [(1815, 2060)],
        "ideology_tags": [],
        "conditions": {},
        "advisors": [
            {
                "name": "Tomasz Wierzbicki",
                "role": "Strike Chairman, Industrial Workers Federation",
                "icon": "✊",
                "option_id": 1,
                "quote": (
                    "Eight hours of work. Eight hours of rest. Eight hours for your family. "
                    "This is not a radical demand — it's arithmetic. "
                    "Our members built every factory in this country with their hands. "
                    "We are asking to see our children before they go to sleep. "
                    "Give us the eight-hour day and we go back Monday morning. Simple."
                ),
            },
            {
                "name": "Baron Friedrich Steinbach",
                "role": "President, Industrial Owners Council",
                "icon": "🏭",
                "option_id": 2,
                "quote": (
                    "These agitators will bankrupt us. Every hour of production lost "
                    "is ground given to our foreign competitors. "
                    "The police exist for exactly this situation, Minister. "
                    "Use them. Make clear that the government will not be held hostage "
                    "by a man in work boots who showed up with a piece of paper. "
                    "Firmness now saves us from chaos later."
                ),
            },
            {
                "name": "Finance Minister Adaeze Okafor",
                "role": "Ministry of Finance",
                "icon": "📊",
                "option_id": 3,
                "quote": (
                    "Nine hours. Not eight, not twelve — nine. "
                    "A small wage increase, an annual review commission, "
                    "and both sides can claim partial victory. "
                    "Wierzbicki gets progress. Steinbach gets stability. "
                    "I get to avoid explaining a general strike to the foreign creditors. "
                    "Everyone wins marginally. That is governance."
                ),
            },
        ],
        "options": [
            {
                "id": 1,
                "text": "Meet all demands — eight-hour day, wage increases",
                "effects": {"stability": 0.08, "happiness": 0.08, "gdp_growth": -0.010, "unemployment": -0.02},
                "flavor": "Workers celebrate in the streets. Productivity, oddly, rises within the month.",
                "news": "Eight-Hour Workday Becomes Law — Labour Calls It Historic Victory",
            },
            {
                "id": 2,
                "text": "Deploy police to break the strike",
                "effects": {"stability": -0.11, "happiness": -0.08, "war_support": 0.04, "prestige": -8},
                "flavor": "The strike is broken. Three workers are killed. "
                          "Wierzbicki calls them martyrs. He is not wrong.",
                "news": "Strike Violently Broken — Three Dead, Unions Vow to Rebuild",
            },
            {
                "id": 3,
                "text": "Negotiate a compromise — nine hours, partial wage rise",
                "effects": {"stability": 0.03, "happiness": 0.03, "gdp_growth": -0.005},
                "flavor": "Both sides grumble extensively. Work resumes Monday.",
                "news": "Compromise Reached — Nine-Hour Day and Wage Review Agreed",
            },
        ],
    },

    # ════════════════════════════════════════════════════════════
    #  CONDITION-TRIGGERED: High unemployment
    # ════════════════════════════════════════════════════════════

    {
        "id": "cond_breadlines",
        "title": "The Breadlines Are Around the Block",
        "description": (
            "Unemployment has reached a level that demographer Dr. Frieda Kranz "
            "describes as 'the kind of number that causes historians to name things after you, "
            "and not in a good way'. Relief kitchens are operating at triple capacity. "
            "The charitable associations running them have sent a letter to the government "
            "that begins: 'We are proud of our mission but this is getting ridiculous.' "
            "A camp of unemployed workers has been set up in the main square "
            "and has, according to city planners, better drainage than the original square."
        ),
        "issue_type": "economic",
        "urgency": "critical",
        "era_years": [(1815, 2060)],
        "ideology_tags": [],
        "conditions": {"min_unemployment": 0.16},
        "advisors": [
            {
                "name": "Dr. Frieda Kranz",
                "role": "Chief Economist, Labour Research Institute",
                "icon": "📈",
                "option_id": 1,
                "quote": (
                    "Public works. Roads, railways, public buildings, drainage — all of it. "
                    "Every worker you employ on a state project is a worker not in the "
                    "breadline, not turning to radical politics, not becoming a historian's "
                    "footnote. Yes it costs money we technically do not have. "
                    "The alternative costs more. History has examples."
                ),
            },
            {
                "name": "Finance Minister Adaeze Okafor",
                "role": "Ministry of Finance",
                "icon": "📊",
                "option_id": 2,
                "quote": (
                    "The problem is structural. Throwing borrowed money at it only kicks "
                    "the problem down the road while creating a debt crisis. "
                    "Cut regulation. Lower corporate taxes. Make it cheaper to hire people. "
                    "Private sector recovery is slower but it is sustainable. "
                    "I know that's hard to explain to the man in the camp with better drainage."
                ),
            },
            {
                "name": "Solidarity Camp Committee",
                "role": "Unemployed Workers' Organisation",
                "icon": "🏕️",
                "option_id": 3,
                "quote": (
                    "We've drawn up a proposal. Minimum wage. Unemployment benefits. "
                    "A housing support fund. Funded by a tax on unearned wealth. "
                    "We've been here for three months. We've had time to work on the details. "
                    "The drainage plan is also available, free of charge."
                ),
            },
        ],
        "options": [
            {
                "id": 1,
                "text": "Emergency public works programme — state-funded mass employment",
                "effects": {"unemployment": -0.05, "stability": 0.05, "gdp_growth": 0.012, "happiness": 0.05},
                "flavor": "Forty thousand workers report to the new works sites on Monday. "
                          "The breadlines shorten noticeably.",
                "news": "Emergency Works Programme Launched — Government to Directly Employ 40,000",
            },
            {
                "id": 2,
                "text": "Deregulation and corporate tax cuts to stimulate private hiring",
                "effects": {"unemployment": -0.02, "stability": -0.03, "gdp_growth": 0.006, "happiness": -0.02},
                "flavor": "Some businesses hire. Many don't. The square camp develops a theatre programme.",
                "news": "Government Bets on Deregulation to Cut Unemployment — Results Mixed",
            },
            {
                "id": 3,
                "text": "Unemployment benefits, minimum wage, and a wealth tax",
                "effects": {"unemployment": -0.03, "stability": 0.06, "happiness": 0.06, "gdp_growth": -0.006},
                "flavor": "The camp dissolves within a month. The drainage plan wins an award.",
                "news": "Safety Net Expansion and Wealth Tax Pass — Business Groups Outraged",
            },
        ],
    },

    {
        "id": "cond_mass_emigration",
        "title": "Everyone is Leaving",
        "description": (
            "The Office of National Statistics has noted, with some delicacy, "
            "that emigration has outpaced immigration for the seventeenth consecutive month. "
            "Skilled workers, young graduates, and several entire families of artisans "
            "are departing for foreign shores at a rate that port administrators "
            "describe as 'brisk'. One shipping company reports its passenger manifests "
            "now read like a professional directory. "
            "The last three people to leave the eastern industrial town of Gravenhal "
            "turned off the lights, posted the keys through the mayor's letterbox, "
            "and caught the 6:15 to the capital."
        ),
        "issue_type": "economic",
        "urgency": "high",
        "era_years": [(1815, 2060)],
        "ideology_tags": [],
        "conditions": {"min_unemployment": 0.13, "max_stability": 0.55},
        "advisors": [
            {
                "name": "Minister of the Interior Greta Möller",
                "role": "Ministry of the Interior",
                "icon": "🚪",
                "option_id": 1,
                "quote": (
                    "We need to make leaving harder. Exit taxes. Mandatory notice periods "
                    "for skilled workers. If the country invested in their education, "
                    "they owe something in return before they board a ship. "
                    "I'm not saying we lock anyone up. I'm saying there should be "
                    "a structured conversation before departure."
                ),
            },
            {
                "name": "Mayor of Gravenhal, Position Vacant",
                "role": "(Position Currently Unmanned)",
                "icon": "🏚️",
                "option_id": 2,
                "quote": (
                    "There is no mayor. The last one emigrated to work in engineering. "
                    "I found this note on my door — I'm the postman, incidentally — "
                    "that says 'fix the economy'. I am passing this along. "
                    "Directly. Please fix the economy. Also the bridge is still broken. "
                    "I'm leaving next Tuesday."
                ),
            },
            {
                "name": "Dr. Frieda Kranz",
                "role": "Labour Research Institute",
                "icon": "📈",
                "option_id": 3,
                "quote": (
                    "People emigrate because the conditions at home are worse than elsewhere. "
                    "Restricting departure is politically catastrophic and historically "
                    "associated with regimes that people prefer not to be remembered as. "
                    "Fix wages. Fix infrastructure. Fix the bridge in Gravenhal. "
                    "The outflow stops when the reason to leave stops."
                ),
            },
        ],
        "options": [
            {
                "id": 1,
                "text": "Exit restrictions — skilled workers must serve notice periods before leaving",
                "effects": {"stability": -0.07, "prestige": -10, "happiness": -0.06},
                "flavor": "The number of people seeking foreign passports through every available channel "
                          "triples overnight. Gravenhal officially empties.",
                "news": "Government Exit Restrictions Backfire — Emigration Accelerates",
            },
            {
                "id": 2,
                "text": "Emergency investment programme in regional towns and infrastructure",
                "effects": {"unemployment": -0.03, "stability": 0.05, "gdp_growth": -0.012, "happiness": 0.04},
                "flavor": "Gravenhal gets its bridge fixed. Some people come back. "
                          "The postman-mayor is re-elected in absentia.",
                "news": "Regional Investment Package Launched — 'Stay and Build' Initiative Begins",
            },
            {
                "id": 3,
                "text": "Improve wages, conditions, and housing to make staying worthwhile",
                "effects": {"unemployment": -0.02, "stability": 0.04, "happiness": 0.05, "gdp_growth": -0.008},
                "flavor": "The emigration rate drops. Several people who already left "
                          "tell their families it's looking better.",
                "news": "Wage and Housing Reforms Aim to Stem Mass Emigration",
            },
        ],
    },

    # ════════════════════════════════════════════════════════════
    #  CONDITION-TRIGGERED: Low stability
    # ════════════════════════════════════════════════════════════

    {
        "id": "cond_revolutionary_pamphlets",
        "title": "The Pamphlets Are Everywhere",
        "description": (
            "Revolutionary pamphlets have been appearing across the capital at a rate "
            "that the secret police chief describes as 'frankly impressive logistics'. "
            "They turn up in government letterboxes, stuck to lampposts, inside "
            "ministry briefings, and — most embarrassingly — inside the sealed "
            "morning papers read by senior officials. "
            "The pamphlets, written by someone calling themselves 'The Voice of the Streets', "
            "are grammatically excellent, well-reasoned, and deeply uncomfortable reading."
        ),
        "issue_type": "political",
        "urgency": "high",
        "era_years": [(1815, 2060)],
        "ideology_tags": [],
        "conditions": {"max_stability": 0.45},
        "advisors": [
            {
                "name": "Director-General Sofía Álvarez",
                "role": "Head of State Security",
                "icon": "🔒",
                "option_id": 1,
                "quote": (
                    "We know who the printer is. We have a general idea of the distribution "
                    "network. Arrest them. Seize the presses. Make an example. "
                    "The pamphlets are good, I'll grant you — whoever wrote them has a "
                    "future in communications — but they are destabilising and we cannot "
                    "let them continue."
                ),
            },
            {
                "name": "\"The Voice of the Streets\"",
                "role": "Anonymous Pamphleteer",
                "icon": "✍️",
                "option_id": 2,
                "quote": (
                    "If the government is embarrassed by what I've written, "
                    "perhaps they should spend less time looking for me and more time "
                    "addressing the conditions I'm writing about. "
                    "I am happy to stop distributing pamphlets the moment the people "
                    "have a legitimate means of being heard. "
                    "Until then, I have a printer, a bicycle, and time."
                ),
            },
            {
                "name": "Chief of Staff Gregor Patel",
                "role": "Chief of Staff",
                "icon": "🗂️",
                "option_id": 3,
                "quote": (
                    "Address the grievances in the pamphlets before they become the "
                    "agenda of something less articulate and more armed. "
                    "Open a public consultation process. Hold town meetings. "
                    "Create a formal channel. The Voice is right on several points — "
                    "I'd prefer not to admit that publicly, but here we are."
                ),
            },
        ],
        "options": [
            {
                "id": 1,
                "text": "Arrest the pamphleteer; seize the printing presses",
                "effects": {"stability": -0.04, "prestige": -8, "happiness": -0.05},
                "flavor": "The Voice of the Streets releases three more pamphlets "
                          "before anyone is arrested. The arrest makes things worse.",
                "news": "Government Arrests Pamphleteer — New Distribution Network Appears Within Days",
            },
            {
                "id": 2,
                "text": "Open a legitimate public consultation process",
                "effects": {"stability": 0.06, "happiness": 0.04, "prestige": 4},
                "flavor": "The pamphlets stop. The Voice submits a thirty-page policy document "
                          "to the consultation. It is, admittedly, quite good.",
                "news": "Public Consultation Launched — Anonymous Pamphleteer Submits Policy Paper",
            },
            {
                "id": 3,
                "text": "Address the specific grievances listed in the pamphlets",
                "effects": {"stability": 0.08, "happiness": 0.06, "gdp_growth": -0.006},
                "flavor": "The pamphlets stop. Several officials privately admit "
                          "they agreed with most of the content.",
                "news": "Government Enacts Reforms Addressing Public Grievances — Pamphlets Cease",
            },
        ],
    },

    {
        "id": "cond_generals_ideas",
        "title": "The Generals Are Having Ideas",
        "description": (
            "Your intelligence service has flagged, with careful diplomatic language, "
            "that senior military officers have been meeting privately, "
            "without agenda or minutes, over the past six weeks. "
            "The meetings always conclude with dinner and port. "
            "Separately, General Kovacs has been giving speeches about "
            "'the failure of civilian leadership in a time of national crisis' "
            "to rooms of junior officers. "
            "The intelligence report is titled, without further elaboration, "
            "'A Situation Worth Monitoring'."
        ),
        "issue_type": "political",
        "urgency": "critical",
        "era_years": [(1815, 2060)],
        "ideology_tags": [],
        "conditions": {"max_stability": 0.35},
        "advisors": [
            {
                "name": "Director-General Sofía Álvarez",
                "role": "Head of State Security",
                "icon": "🔒",
                "option_id": 1,
                "quote": (
                    "Reassign Kovacs immediately. Separate the meeting group. "
                    "Replace the most senior officers with loyalists and make clear — "
                    "politely but unambiguously — that the military exists to defend "
                    "the state, not to govern it. Do it before the next dinner party."
                ),
            },
            {
                "name": "General Alexei Kovacs",
                "role": "Chief of the General Staff",
                "icon": "⚔️",
                "option_id": 2,
                "quote": (
                    "I am concerned about national stability. As is my duty. "
                    "The current civilian leadership has demonstrated a remarkable "
                    "capacity for inaction in a time of crisis. "
                    "The armed forces stand ready to ensure the continuity of governance. "
                    "That is all I'm prepared to say on the record."
                ),
            },
            {
                "name": "Chief of Staff Gregor Patel",
                "role": "Chief of Staff",
                "icon": "🗂️",
                "option_id": 3,
                "quote": (
                    "The generals are having ideas because there's a vacuum. "
                    "Fill the vacuum. Decisive action on the actual crisis — "
                    "announce something significant this week, show leadership, "
                    "give the population something to rally behind. "
                    "Kovacs loses his audience when the civilian government "
                    "is visibly in charge and visibly doing something."
                ),
            },
        ],
        "options": [
            {
                "id": 1,
                "text": "Reassign Kovacs; restructure military leadership with loyal officers",
                "effects": {"stability": 0.04, "war_support": -0.05, "prestige": 2},
                "flavor": "Kovacs accepts the reassignment in stony silence. "
                          "The dinner meetings stop. Port consumption in the officer's mess drops.",
                "news": "Military Leadership Shakeup — Senior Generals Reassigned",
            },
            {
                "id": 2,
                "text": "Open direct talks with Kovacs — understand what the military wants",
                "effects": {"stability": -0.02, "war_support": 0.05, "prestige": -4},
                "flavor": "Kovacs presents a list of demands. Several are reasonable. "
                          "The last one is about 'enhanced operational authority'. You decline that one.",
                "news": "Government in Emergency Talks With Military Leadership",
            },
            {
                "id": 3,
                "text": "Make decisive public announcements to restore civilian authority",
                "effects": {"stability": 0.07, "happiness": 0.04, "prestige": 6},
                "flavor": "A week of strong, visible governance later, the dinner parties stop. "
                          "Kovacs gives a speech about the 'resilience of democratic institutions'. "
                          "Nobody believes him, but the crisis passes.",
                "news": "Government Announces Major Reform Package — Military 'Concerns' Subside",
            },
        ],
    },

    # ════════════════════════════════════════════════════════════
    #  CONDITION-TRIGGERED: At war
    # ════════════════════════════════════════════════════════════

    {
        "id": "cond_deserters",
        "title": "The Deserters in the Capital",
        "description": (
            "Military police have been quietly rounding up deserters in the capital "
            "for three weeks, with limited success. General Kovacs reports that "
            "the number of men who have 'gone missing' from front-line units "
            "has reached four figures. Most appear to have returned home. "
            "A significant number are reportedly running small businesses. "
            "One has been elected to a local council on a platform of "
            "'bringing common sense to governance', which Kovacs considers ironic."
        ),
        "issue_type": "military",
        "urgency": "high",
        "era_years": [(1815, 2060)],
        "ideology_tags": [],
        "conditions": {"at_war": True},
        "advisors": [
            {
                "name": "General Alexei Kovacs",
                "role": "Chief of the General Staff",
                "icon": "⚔️",
                "option_id": 1,
                "quote": (
                    "Courts-martial. Every one of them. If we allow desertion to go "
                    "unpunished, we have no army — we have a suggestion. "
                    "The men at the front deserve to know that the man beside them "
                    "will stay. Make an example. It is unpleasant but necessary."
                ),
            },
            {
                "name": "Councillor Bertrand Falks",
                "role": "Former Deserter, Newly Elected Local Councillor",
                "icon": "🗳️",
                "option_id": 2,
                "quote": (
                    "I have seen what we are asking those men to endure. I have done it. "
                    "I left because I am not ready to die for a line on a map. "
                    "I suspect most of my colleagues left for the same reason. "
                    "If the cause is just, then make the case for it. "
                    "If it isn't, perhaps reconsider the war."
                ),
            },
            {
                "name": "General Miriam Osei",
                "role": "Director, Military Welfare Command",
                "icon": "🎖️",
                "option_id": 3,
                "quote": (
                    "Punishment alone won't work — Kovacs knows this, he just won't say it. "
                    "Better conditions at the front, clearer communication of war aims, "
                    "and an amnesty for first-time deserters who return voluntarily. "
                    "You want men who choose to fight, not men who fight to avoid punishment. "
                    "One of those armies is better."
                ),
            },
        ],
        "options": [
            {
                "id": 1,
                "text": "Courts-martial all deserters as an example",
                "effects": {"war_support": 0.06, "stability": -0.06, "happiness": -0.06},
                "flavor": "The trials are public. Desertion drops. Re-enlistment also drops. "
                          "Councillor Falks is not charged — he was already elected.",
                "news": "Military Courts-Martial Launched for Hundreds of Deserters",
            },
            {
                "id": 2,
                "text": "Amnesty for deserters who return voluntarily; improve front conditions",
                "effects": {"war_support": -0.02, "stability": 0.04, "happiness": 0.03, "morale": 0.05},
                "flavor": "Most deserters return. Kovacs is professionally furious. "
                          "Morale at the front — measured by letter volume — improves.",
                "news": "Government Offers Deserter Amnesty — Thousands Return to Front",
            },
            {
                "id": 3,
                "text": "Accept the losses; focus resources on the willing troops",
                "effects": {"war_support": -0.05, "stability": 0.02, "morale": 0.03},
                "flavor": "A smaller, more committed force. Kovacs calls it 'manageable'.",
                "news": "Military Quietly Accepts Desertion Losses — Focus Shifts to Volunteer Force",
            },
        ],
    },

    {
        "id": "cond_war_profiteers",
        "title": "Someone Is Making a Lot of Money From This War",
        "description": (
            "An parliamentary audit committee has discovered that the contracts awarded "
            "for military supplies — boots, blankets, ammunition, and field rations — "
            "have been granted almost exclusively to a holding company called "
            "Patriot Supply Group, which did not exist eighteen months ago "
            "and whose board of directors includes the brother-in-law of "
            "the Procurement Minister. The boots have been described by soldiers "
            "as 'structurally ambitious' and the field rations as 'theoretically food'."
        ),
        "issue_type": "political",
        "urgency": "high",
        "era_years": [(1815, 2060)],
        "ideology_tags": [],
        "conditions": {"at_war": True},
        "advisors": [
            {
                "name": "Audit Committee Chair Vera Lindemann",
                "role": "Parliamentary Audit Committee",
                "icon": "📋",
                "option_id": 1,
                "quote": (
                    "The contracts must be cancelled. The Procurement Minister must resign. "
                    "The company must be investigated for fraud. "
                    "We are sending soldiers to war in boots that fall apart "
                    "and feeding them rations that the committee's intern described "
                    "as 'a philosophical experience'. "
                    "This is corruption and soldiers are dying for it."
                ),
            },
            {
                "name": "Procurement Minister Benedict Harlow",
                "role": "Ministry of Procurement",
                "icon": "📜",
                "option_id": 2,
                "quote": (
                    "My brother-in-law's company submitted the lowest tender. "
                    "That is how procurement works. The boots are within specification — "
                    "I have the specification documents here, and the specification "
                    "is admittedly quite flexible. This is a political attack "
                    "orchestrated by my enemies and I will be challenging these findings "
                    "through the appropriate channels."
                ),
            },
            {
                "name": "Sergeant-Major Anya Petrov",
                "role": "First Infantry Division",
                "icon": "🪖",
                "option_id": 3,
                "quote": (
                    "My left boot dissolved in the rain last Tuesday. "
                    "I have it here if anyone wants to see it. "
                    "Or what's left of it. I'm not asking for philosophy. "
                    "I'm asking for boots that survive contact with mud. "
                    "Whatever you do up there, please do it quickly."
                ),
            },
        ],
        "options": [
            {
                "id": 1,
                "text": "Cancel contracts; sack the minister; open fraud investigation",
                "effects": {"stability": 0.07, "prestige": 10, "war_support": 0.04, "happiness": 0.04},
                "flavor": "New contracts are awarded. The boots, by the following month, "
                          "are functional. The minister is awaiting trial.",
                "news": "Procurement Scandal: Minister Sacked, Fraud Investigation Launched",
            },
            {
                "id": 2,
                "text": "Accept the minister's explanation; internal review only",
                "effects": {"stability": -0.08, "prestige": -12, "war_support": -0.06},
                "flavor": "The audit committee publishes a blistering second report. "
                          "Sergeant-Major Petrov sends her dissolved boot to the press.",
                "news": "Government Clears Procurement Minister — Opposition Calls It a Whitewash",
            },
            {
                "id": 3,
                "text": "Emergency re-procurement from new suppliers; restructure the ministry",
                "effects": {"stability": 0.03, "war_support": 0.05, "gdp_growth": -0.008, "prestige": 4},
                "flavor": "New suppliers are found within a week. The boots are, by all accounts, "
                          "boots. The soldiers are grateful.",
                "news": "War Supplies Overhauled After Corruption Scandal — Minister Steps Aside",
            },
        ],
    },

    # ════════════════════════════════════════════════════════════
    #  CONDITION-TRIGGERED: High world tension
    # ════════════════════════════════════════════════════════════

    {
        "id": "cond_spy_discovered",
        "title": "We Have Found Someone Else's Spy",
        "description": (
            "Intelligence services have arrested a foreign national named Klaus Brandt, "
            "who had been working as a second assistant cataloguer at the National Archive "
            "for eleven years without incident. A routine audit discovered he had "
            "photographed approximately 40,000 classified documents during this time, "
            "which the intelligence chief describes as 'a remarkable work ethic "
            "in service of the wrong country'. "
            "Brandt himself, when confronted, reportedly said 'fair enough' and asked "
            "if he could finish filing the Bs."
        ),
        "issue_type": "diplomatic",
        "urgency": "high",
        "era_years": [(1815, 2060)],
        "ideology_tags": [],
        "conditions": {"min_world_tension": 0.45},
        "advisors": [
            {
                "name": "Director-General Sofía Álvarez",
                "role": "Head of State Security",
                "icon": "🔒",
                "option_id": 1,
                "quote": (
                    "Expel their ambassador. Declare three of their diplomats persona non grata. "
                    "Put Brandt on trial for espionage. This is a public act of aggression "
                    "against our sovereignty and it requires a public response. "
                    "Otherwise every other foreign service in the world notes that "
                    "we are a soft target."
                ),
            },
            {
                "name": "Ambassador Chen Wei",
                "role": "Foreign Affairs Advisor",
                "icon": "🌐",
                "option_id": 2,
                "quote": (
                    "Diplomatic expulsion escalates. A quiet exchange — Brandt for "
                    "one of our people currently in their custody for reasons we "
                    "don't discuss publicly — resolves the situation without "
                    "inflaming tensions that are already, as you know, quite warm. "
                    "Also, we find out what they know."
                ),
            },
            {
                "name": "Archive Director Ingrid Moser",
                "role": "National Archive",
                "icon": "📚",
                "option_id": 3,
                "quote": (
                    "He photographed forty thousand documents. Forty thousand. "
                    "He had a special camera hidden in his cardigan. "
                    "Whatever you decide diplomatically, please also modernise our "
                    "security protocols. He has been here since my predecessor's predecessor. "
                    "He knew where everything was. He was very helpful with the Bs."
                ),
            },
        ],
        "options": [
            {
                "id": 1,
                "text": "Publicly expel diplomats; put Brandt on trial",
                "effects": {"world_tension": 0.08, "prestige": 5, "stability": -0.02},
                "flavor": "The trial is very public. The foreign power expels three of our diplomats. "
                          "Brandt is found guilty and seems unsurprised.",
                "news": "Spy Scandal: Diplomats Expelled, Espionage Trial Opens",
            },
            {
                "id": 2,
                "text": "Quiet prisoner exchange; resolve diplomatically without public confrontation",
                "effects": {"world_tension": -0.04, "prestige": 2, "stability": 0.01},
                "flavor": "Brandt is swapped at a border crossing at 3am. "
                          "Nobody confirms the exchange officially. Brandt's files are reviewed.",
                "news": "Archive Spy Quietly Expelled — Diplomatic Sources Hint at Exchange",
            },
            {
                "id": 3,
                "text": "Use as leverage — negotiate intelligence-sharing agreement",
                "effects": {"world_tension": -0.02, "prestige": 4, "stability": 0.02},
                "flavor": "Three months of talks later, an agreement is in place. "
                          "Brandt returns home. The Bs are finally fully catalogued.",
                "news": "Spy Arrest Becomes Intelligence Leverage — Bilateral Agreement Signed",
            },
        ],
    },

    # ════════════════════════════════════════════════════════════
    #  CHAINED ISSUES
    # ════════════════════════════════════════════════════════════

    {
        "id": "chain_underground_music",
        "title": "The Underground Music Scene is Thriving",
        "description": (
            "Following the government's regulation of artistic content, "
            "an underground music movement has exploded. "
            "Venues operating without licences, press-printed concert programmes "
            "on stolen paper, and musicians going by pseudonyms have transformed "
            "the city's basements and back rooms into a cultural phenomenon. "
            "Wally Eigendorf is apparently headlining under the name 'Artistically Expressed' "
            "and the shows are, according to everyone who attends, extremely good. "
            "The Culture Standards Bureau is not having a great month."
        ),
        "issue_type": "social",
        "urgency": "normal",
        "era_years": [(1900, 2060)],
        "ideology_tags": [],
        "chains_from": {"issue_id": "u_rap_trial", "option_id": 3},
        "conditions": {},
        "advisors": [
            {
                "name": "Bureau Director Elspeth Crane",
                "role": "Culture Standards Bureau",
                "icon": "📋",
                "option_id": 1,
                "quote": (
                    "We need enforcement authority. Licence inspections. "
                    "The ability to shut down unlicenced venues. "
                    "I understand the optics of the Culture Bureau shutting down "
                    "music in basements, but if we don't enforce our standards "
                    "we might as well not have them. "
                    "Also — and I say this professionally — the music is actually "
                    "quite good, which makes this harder."
                ),
            },
            {
                "name": "'Artistically Expressed' (Wally Eigendorf)",
                "role": "Underground Musician",
                "icon": "🎤",
                "option_id": 2,
                "quote": (
                    "The more you try to stop this, the bigger we get. "
                    "Last week we had eight hundred people in a former warehouse. "
                    "You cannot contain art, you know what I mean? "
                    "Just... legalise it. Come to a show. I'll put you on the list. "
                    "The Bureau lady can come too."
                ),
            },
            {
                "name": "Jonas Pfeiffer-Quinn",
                "role": "Classical Guitarist",
                "icon": "🎸",
                "option_id": 3,
                "quote": (
                    "I went. To a show. Purely for research purposes. "
                    "It was eight hundred people in a basement and I am not going "
                    "to say I enjoyed it because my reputation wouldn't survive. "
                    "But the energy in that room was genuinely extraordinary. "
                    "Perhaps the Bureau's standards are not the only standard."
                ),
            },
        ],
        "options": [
            {
                "id": 1,
                "text": "Give the Bureau enforcement powers; crack down on unlicenced venues",
                "effects": {"stability": -0.05, "happiness": -0.04, "prestige": -6},
                "flavor": "Raids begin. The music moves to even smaller venues. "
                          "Wally Eigendorf releases an album about being raided. "
                          "It is extremely good.",
                "news": "Culture Bureau Raids Underground Music Venues — Scene Goes Deeper Underground",
            },
            {
                "id": 2,
                "text": "Liberalise arts regulations; grant amnesty to unlicenced venues",
                "effects": {"stability": 0.04, "happiness": 0.05, "prestige": 5},
                "flavor": "The Bureau pivots to a 'facilitating role'. The underground scene "
                          "moves overground. Wally Eigendorf wins an arts grant.",
                "news": "Arts Regulations Relaxed — Underground Music Scene Goes Mainstream",
            },
            {
                "id": 3,
                "text": "Abolish the Culture Standards Bureau entirely",
                "effects": {"stability": 0.06, "happiness": 0.06, "prestige": 3, "gdp_growth": 0.003},
                "flavor": "The Bureau staff are redeployed. A cultural explosion follows. "
                          "Jonas Pfeiffer-Quinn is spotted at three Wally shows. He maintains it was research.",
                "news": "Culture Bureau Abolished — Artistic Freedom Restored",
            },
        ],
    },

    {
        "id": "chain_nurses_strike",
        "title": "The Nurses Have Had Enough",
        "description": (
            "In the months following the healthcare expansion, the nurses of the "
            "new national system have formally notified the government of strike action. "
            "Their chief complaint, delivered in a letter co-signed by 14,000 nurses "
            "and the entire ward staff of Central Hospital, is that the new system "
            "has dramatically increased their workload without a corresponding "
            "increase in pay or staffing. "
            "Dr. Vasquez, who championed the expansion, has — not without some awkwardness — "
            "added her signature to the letter."
        ),
        "issue_type": "social",
        "urgency": "high",
        "era_years": [(1815, 2060)],
        "ideology_tags": [],
        "chains_from": {"issue_id": "u_healthcare_birth", "option_id": 1},
        "conditions": {},
        "advisors": [
            {
                "name": "Chief Nurse Adanna Osei",
                "role": "Nursing Union, National Strike Committee",
                "icon": "🏥",
                "option_id": 1,
                "quote": (
                    "We supported the expansion. We still support universal healthcare. "
                    "But we are working sixteen-hour shifts because you built the system "
                    "without building the workforce to run it. "
                    "We need more nurses, better pay, and safe staffing ratios, "
                    "in writing, before Monday. Or the wards are empty Monday morning."
                ),
            },
            {
                "name": "Finance Minister Adaeze Okafor",
                "role": "Ministry of Finance",
                "icon": "📊",
                "option_id": 2,
                "quote": (
                    "The healthcare expansion is already straining the budget. "
                    "I support the nurses in principle — I do — but we cannot simply "
                    "double the nursing payroll overnight. A phased approach. "
                    "A three-year hiring plan. Modest pay increases now, larger ones "
                    "when the economic case supports them. Sustainable governance."
                ),
            },
            {
                "name": "Dr. Elena Vasquez",
                "role": "Chief of Medicine, Central Hospital",
                "icon": "👩‍⚕️",
                "option_id": 3,
                "quote": (
                    "I signed the letter. I'll be honest about why: I told you we'd "
                    "need more staff when we expanded and it didn't happen. "
                    "So yes, I'm with the nurses. But I also think there's a third way: "
                    "international recruitment. We can hire trained nurses from abroad "
                    "quickly, bridge the staffing gap, and negotiate pay increases "
                    "without breaking the budget immediately."
                ),
            },
        ],
        "options": [
            {
                "id": 1,
                "text": "Meet demands in full — immediate pay rise and rapid staffing increase",
                "effects": {"stability": 0.05, "happiness": 0.06, "gdp_growth": -0.014},
                "flavor": "The strike is called off Monday morning. "
                          "Adanna Osei shakes hands with the Health Minister and goes back to work.",
                "news": "Nurses' Demands Met — Strike Averted, Pay Rise Confirmed",
            },
            {
                "id": 2,
                "text": "Offer phased pay increases over three years",
                "effects": {"stability": -0.03, "happiness": -0.04, "gdp_growth": -0.006},
                "flavor": "The nurses strike for two weeks. Patients are moved to private facilities. "
                          "The political cost is significant.",
                "news": "Nurses Strike Begins — Government Offers Slow-Phase Compromise Rejected",
            },
            {
                "id": 3,
                "text": "International recruitment drive plus modest immediate pay rise",
                "effects": {"stability": 0.03, "happiness": 0.03, "gdp_growth": -0.009, "unemployment": -0.01},
                "flavor": "Foreign nurses begin arriving within six weeks. "
                          "Dr. Vasquez declares herself 'cautiously satisfied', which is high praise.",
                "news": "International Nurse Recruitment Launched — Strike Narrowly Averted",
            },
        ],
    },

    # ════════════════════════════════════════════════════════════
    #  ERA-SPECIFIC: WWII
    # ════════════════════════════════════════════════════════════

    {
        "id": "ww2_german_demand",
        "title": "Hitler Demands the Border Territories",
        "description": (
            "A telegram has arrived from Berlin, personally signed. "
            "Adolf Hitler, Chancellor of the German Reich, "
            "demands the immediate cession of the Sudetenland — "
            "the German-speaking border regions — to the Reich. "
            "He describes it as 'the last territorial demand I shall make in Europe'. "
            "Your ambassador in Berlin notes this is the fourth time "
            "the word 'last' has been used in a German ultimatum in the past eighteen months. "
            "The Wehrmacht is on the move. Britain and France are counselling patience."
        ),
        "issue_type": "diplomatic",
        "urgency": "critical",
        "era_years": [(1936, 1943)],
        "ideology_tags": [],
        "conditions": {},
        "advisors": [
            {
                "name": "General Alexei Kovacs",
                "role": "Chief of the General Staff",
                "icon": "⚔️",
                "option_id": 1,
                "quote": (
                    "Every concession teaches him that threats work. "
                    "He demanded the Rhineland. We gave it. Austria. We watched. "
                    "This territory will not be the last. The next telegram will have "
                    "a different country in the subject line. "
                    "Mobilise. Draw the line. The cost now is less than the cost later."
                ),
            },
            {
                "name": "Prime Minister Lord Chamberlain",
                "role": "Diplomatic Advisor",
                "icon": "🎩",
                "option_id": 2,
                "quote": (
                    "We are not ready for a European war. Our rearmament programme "
                    "needs twelve more months at minimum. "
                    "A year of peace — bought even at this price — is a year in which "
                    "we build aircraft, train soldiers, and fortify our positions. "
                    "Sometimes wisdom looks like weakness. This is one of those times. "
                    "I believe he means it when he says last."
                ),
            },
            {
                "name": "Ambassador Chen Wei",
                "role": "Foreign Affairs Advisor",
                "icon": "🌐",
                "option_id": 3,
                "quote": (
                    "Propose an internationally supervised plebiscite in the contested territories. "
                    "Let the people who live there vote on sovereignty. "
                    "If Hitler refuses impartial process, his true intentions are revealed "
                    "to the world without a single shot being fired. "
                    "We gain the moral high ground and international solidarity. "
                    "It will probably not stop him. But it will matter later."
                ),
            },
        ],
        "options": [
            {
                "id": 1,
                "text": "Refuse — mobilise forces and stand with the threatened nation",
                "effects": {"war_support": 0.14, "stability": -0.04, "prestige": 12, "world_tension": 0.14},
                "flavor": "Europe holds its breath. The Wehrmacht pauses. "
                          "Hitler calls it 'a temporary complication'. He means it.",
                "news": "Government Defies Berlin Ultimatum — Forces Mobilised in Solidarity",
            },
            {
                "id": 2,
                "text": "Concede the territories — accept Hitler's 'last demand'",
                "effects": {"war_support": -0.08, "stability": 0.02, "prestige": -16, "world_tension": -0.05},
                "flavor": "The Czech government is not consulted. The next telegram arrives in six months.",
                "news": "Territories Ceded to Berlin — 'Peace for Our Time', Says Government",
            },
            {
                "id": 3,
                "text": "Propose international plebiscite under neutral supervision",
                "effects": {"war_support": 0.04, "stability": 0.01, "prestige": 7, "world_tension": 0.04},
                "flavor": "Berlin rejects the plebiscite. The world notes the rejection. "
                          "Time is bought. Not much time. But some.",
                "news": "Plebiscite Proposal Rejected by Berlin — International Unity Grows",
            },
        ],
    },

    {
        "id": "ww2_resistance",
        "title": "A Young Woman Arrived at the Embassy at Dawn",
        "description": (
            "Her name is Marta. She is twenty-two, she has walked for six days, "
            "and she is carrying a message from the resistance fighters operating "
            "inside occupied territory. They have derailed eleven supply trains, "
            "sheltered over two hundred escaped prisoners of war, and are running "
            "a printing press in a bakery that the occupying forces have inspected "
            "four times. They need weapons, radios, and one trained wireless operator. "
            "Your intelligence chief has laid out both the opportunity and the considerable risks."
        ),
        "issue_type": "diplomatic",
        "urgency": "high",
        "era_years": [(1939, 1946)],
        "ideology_tags": [],
        "conditions": {},
        "advisors": [
            {
                "name": "Colonel Marcus Wren",
                "role": "Director, Special Operations",
                "icon": "🎖️",
                "option_id": 1,
                "quote": (
                    "Every train they derail is a train that does not reach the front. "
                    "Every escaped prisoner they shelter is a pilot or a sergeant "
                    "who might fight again. This is asymmetric warfare at its best — "
                    "it costs us a fraction of a conventional division. "
                    "Support them. Give Marta everything she asked for."
                ),
            },
            {
                "name": "Ambassador Chen Wei",
                "role": "Foreign Affairs Advisor",
                "icon": "🌐",
                "option_id": 2,
                "quote": (
                    "If this operation is discovered — and eventually it will be — "
                    "the occupying force will use it as justification for reprisals "
                    "against the civilian population. We've seen this pattern before. "
                    "I'm not saying do nothing. I'm saying be cautious about "
                    "what we send and how traceable we are."
                ),
            },
            {
                "name": "Marta",
                "role": "Resistance Courier",
                "icon": "🌿",
                "option_id": 3,
                "quote": (
                    "I walked for six days. I am asking for radios and a wireless operator. "
                    "Forty people are living in that bakery right now and they believe "
                    "someone is coming to help them. "
                    "I will walk back the same way I came. "
                    "I just need to know what to tell them."
                ),
            },
        ],
        "options": [
            {
                "id": 1,
                "text": "Full support — weapons, radios, and trained agents",
                "effects": {"war_support": 0.08, "prestige": 6, "stability": -0.02, "world_tension": 0.04},
                "flavor": "The bakery press runs faster. The supply lines become "
                          "increasingly unreliable for the occupiers.",
                "news": "Resistance Forces Report Major Operations Behind Enemy Lines",
            },
            {
                "id": 2,
                "text": "Covert support through neutral intermediaries — deniable",
                "effects": {"war_support": 0.04, "prestige": 3, "stability": -0.01},
                "flavor": "The weapons arrive via three different countries. "
                          "Nobody can prove where they came from.",
                "news": "Resistance Receives Mysterious Arms Shipment — Source Denied",
            },
            {
                "id": 3,
                "text": "Send Marta back with humanitarian supplies only — no weapons",
                "effects": {"war_support": -0.03, "prestige": -4, "stability": 0.01},
                "flavor": "Marta accepts the decision without expression and walks back. "
                          "The bakery continues. The trains continue.",
                "news": "Government Declines to Arm Resistance — Aid Package Sent Instead",
            },
        ],
    },

    {
        "id": "ww2_conscription",
        "title": "The Casualty Lists Are Getting Longer",
        "description": (
            "The front-line units are reporting casualty rates that the War Ministry "
            "describes, with considerable understatement, as 'challenging to sustain'. "
            "Volunteer recruitment has slowed to a trickle. "
            "General Kovacs has placed a conscription bill on your desk with a single "
            "cover note: 'The mathematics are simple.' "
            "The labour unions have placed a counter-note on top of it: "
            "'The mathematics are also simple from where we're standing.'"
        ),
        "issue_type": "military",
        "urgency": "critical",
        "era_years": [(1914, 1946)],
        "ideology_tags": [],
        "conditions": {"at_war": True},
        "advisors": [
            {
                "name": "General Alexei Kovacs",
                "role": "Chief of the General Staff",
                "icon": "⚔️",
                "option_id": 1,
                "quote": (
                    "Every week we debate this, the casualty lists grow. "
                    "Our enemies conscripted two years ago. "
                    "The men at the front are holding a line with fraying equipment "
                    "and diminishing numbers. "
                    "Sign the order. We can discuss philosophy after we win."
                ),
            },
            {
                "name": "Karl Baumann",
                "role": "Chairman, United Labour Federation",
                "icon": "✊",
                "option_id": 2,
                "quote": (
                    "You will send working men to die in a war that could be ended "
                    "at a negotiating table. "
                    "We will strike. Every factory, every railway, every port. "
                    "I don't say this lightly. I say it because the men you want "
                    "to conscript deserve to have someone say it."
                ),
            },
            {
                "name": "Finance Minister Adaeze Okafor",
                "role": "Ministry of Finance",
                "icon": "📊",
                "option_id": 3,
                "quote": (
                    "National service — not just military. Men who serve in munitions, "
                    "on railways, in hospitals, in fields — all contributing, "
                    "all counted, all recognised. You get the manpower both at the front "
                    "and in the factories. The union can object less to 'national service' "
                    "than to 'conscription'. Words matter."
                ),
            },
        ],
        "options": [
            {
                "id": 1,
                "text": "Introduce immediate full military conscription",
                "effects": {"war_support": 0.12, "stability": -0.08, "happiness": -0.06},
                "flavor": "A million new recruits. A million furious families. "
                          "The front holds.",
                "news": "Universal Conscription Announced — Protests in Major Cities",
            },
            {
                "id": 2,
                "text": "Refuse conscription; seek ceasefire negotiations",
                "effects": {"war_support": -0.15, "stability": 0.04, "prestige": -14},
                "flavor": "The front deteriorates. Allies are furious. "
                          "The killing slows, eventually.",
                "news": "Government Rejects Conscription — Seeks Armistice Talks",
            },
            {
                "id": 3,
                "text": "National service act — military or industrial posting by choice",
                "effects": {"war_support": 0.07, "stability": -0.03, "happiness": -0.02, "gdp_growth": 0.008},
                "flavor": "Shell production doubles within six months. "
                          "The army grows. The unions accept it, narrowly.",
                "news": "National Service Act Passes — Citizens to Choose Military or Industrial Duty",
            },
        ],
    },

    # ════════════════════════════════════════════════════════════
    #  ECONOMIC ISSUES
    # ════════════════════════════════════════════════════════════

    {
        "id": "eco_recession",
        "title": "The Economy Is Doing What Economists Warned It Might Do",
        "description": (
            "GDP growth has turned negative for the first time in a decade. "
            "Chief Economist Dr. Frieda Kranz has published a report that begins "
            "'I told you so' — she insists this is a technical term — "
            "and runs to forty-seven pages. "
            "The unemployment queues have been described by the Minister of Labour "
            "as 'longer than is comfortable to look at'. "
            "Three different schools of economic thought have sent representatives "
            "to your office, and they agree on nothing except that they are right "
            "and the other two are dangerously wrong."
        ),
        "issue_type": "economic",
        "urgency": "high",
        "era_years": [(1815, 2060)],
        "ideology_tags": [],
        "conditions": {"max_gdp_growth": 0.0},
        "advisors": [
            {
                "name": "Dr. Frieda Kranz",
                "role": "Chief Economist",
                "icon": "📈",
                "option_id": 1,
                "quote": (
                    "Spend. Now. Government investment in infrastructure, "
                    "public services, direct employment. "
                    "In a recession, private capital retreats — so the state must "
                    "advance. This is not radicalism. This is the textbook. "
                    "I can show you the textbook. I wrote several pages of it."
                ),
            },
            {
                "name": "Baron Friedrich Steinbach",
                "role": "President, Industrial Owners Council",
                "icon": "🏭",
                "option_id": 2,
                "quote": (
                    "Cut spending. Balance the budget. Let weak businesses fail — "
                    "that is how markets correct. "
                    "Government stimulus creates debt that crushes the next generation. "
                    "This is painful but necessary. "
                    "Also, please cut our taxes. This is slightly separate advice "
                    "but I'm here so I thought I'd mention it."
                ),
            },
            {
                "name": "Finance Minister Adaeze Okafor",
                "role": "Ministry of Finance",
                "icon": "📊",
                "option_id": 3,
                "quote": (
                    "Targeted foreign investment. Lower barriers, simplified licensing, "
                    "a streamlined investment visa. "
                    "We let foreign capital do what domestic capital won't right now. "
                    "It's not perfect and there are sovereignty implications I'm happy "
                    "to discuss at length at another time. "
                    "But it doesn't require borrowing and it generates employment."
                ),
            },
        ],
        "options": [
            {
                "id": 1,
                "text": "State stimulus — government investment and direct employment",
                "effects": {"gdp_growth": 0.022, "unemployment": -0.03, "stability": 0.04, "happiness": 0.04},
                "flavor": "Recovery is slow but genuine. Dr. Kranz publishes a follow-up report "
                          "titled 'As I Said'.",
                "news": "Government Stimulus Package Announced — Growth Begins to Return",
            },
            {
                "id": 2,
                "text": "Austerity — cut spending; let the market correct itself",
                "effects": {"gdp_growth": -0.008, "stability": -0.07, "happiness": -0.07, "unemployment": 0.05},
                "flavor": "The market eventually corrects. The social cost is very high "
                          "and very unevenly distributed.",
                "news": "Austerity Programme Begins — Economists Divided on Wisdom",
            },
            {
                "id": 3,
                "text": "Open economy to foreign investment with streamlined licensing",
                "effects": {"gdp_growth": 0.012, "trade_openness": 0.06, "unemployment": -0.02, "prestige": 2},
                "flavor": "Foreign capital arrives. Recovery is real but dependent. "
                          "Steinbach objects that it isn't his capital doing the recovering.",
                "news": "Economy Opens to Foreign Investment — Recovery Begins",
            },
        ],
    },

    # ════════════════════════════════════════════════════════════
    #  MODERN ERA
    # ════════════════════════════════════════════════════════════

    {
        "id": "mod_social_media",
        "title": "The Internet Is Radicalising Someone",
        "description": (
            "A parliamentary committee has published a report confirming what most people "
            "already suspected: a significant portion of the population is spending "
            "between six and nine hours a day on social media platforms "
            "and emerging angrier than they went in. "
            "Three major platforms have declined to appear before the committee, "
            "citing scheduling conflicts. "
            "The committee chair, MP Dorota Rybak, held up a phone during the hearing "
            "and said 'this thing is doing something to us' in a tone that suggested "
            "she wasn't entirely sure what but was quite worried about it."
        ),
        "issue_type": "political",
        "urgency": "normal",
        "era_years": [(2000, 2060)],
        "ideology_tags": [],
        "conditions": {},
        "advisors": [
            {
                "name": "MP Dorota Rybak",
                "role": "Parliamentary Technology Committee Chair",
                "icon": "📱",
                "option_id": 1,
                "quote": (
                    "Regulate. Liability for algorithmic harm. "
                    "Mandatory transparency on recommendation systems. "
                    "A duty of care from platforms to their users — the same legal obligation "
                    "we put on anyone else whose product repeatedly injures people. "
                    "This is not censorship. It is the bare minimum of consumer protection."
                ),
            },
            {
                "name": "Platform Representative (via video call)",
                "role": "Global Tech Consortium",
                "icon": "💻",
                "option_id": 2,
                "quote": (
                    "We take user wellbeing extremely seriously. "
                    "We have a team of fourteen thousand people working on it. "
                    "We believe strongly in free expression and user choice. "
                    "We would welcome the opportunity to continue self-regulating. "
                    "The committee's concerns are noted and we'll be sending a longer "
                    "letter with some graphs. Thank you for your time. "
                    "[Call ends]"
                ),
            },
            {
                "name": "Professor Yuna Park",
                "role": "Digital Sociology Institute",
                "icon": "🔬",
                "option_id": 3,
                "quote": (
                    "The platforms aren't the cause — they're the amplifier. "
                    "People who are economically insecure and socially isolated "
                    "are extremely susceptible to online radicalisation. "
                    "Regulate the platforms, yes. But also address the underlying "
                    "conditions. It's slower and less satisfying than blaming an algorithm, "
                    "but it's more accurate."
                ),
            },
        ],
        "options": [
            {
                "id": 1,
                "text": "Platform liability laws and algorithmic transparency requirements",
                "effects": {"stability": 0.03, "happiness": 0.02, "prestige": 5, "gdp_growth": -0.003},
                "flavor": "Three platforms threaten to leave the country. "
                          "One actually does. Nobody misses it as much as anticipated.",
                "news": "Social Media Liability Law Passes — Platforms Threaten to Leave",
            },
            {
                "id": 2,
                "text": "Accept industry self-regulation; await the letter with graphs",
                "effects": {"stability": -0.03, "happiness": -0.02, "prestige": -4},
                "flavor": "The letter arrives. It has very impressive graphs. "
                          "Nothing changes. MP Rybak is not surprised.",
                "news": "Government Accepts Platform Self-Regulation — Critics Call It a Capitulation",
            },
            {
                "id": 3,
                "text": "Social and economic reform alongside platform regulation",
                "effects": {"stability": 0.05, "happiness": 0.04, "gdp_growth": -0.008, "prestige": 4},
                "flavor": "A long game. The radicalisation rate drops over three years. "
                          "MP Rybak is cautiously pleased.",
                "news": "Government Targets Radicalisation With Dual Social and Tech Reform",
            },
        ],
    },

    # ════════════════════════════════════════════════════════════
    #  LOW STABILITY + IDEOLOGY-SPECIFIC
    # ════════════════════════════════════════════════════════════

    {
        "id": "ideo_nationalist_march",
        "title": "The March That Grew Overnight",
        "description": (
            "A nationalist movement that organised what it described as 'a small cultural "
            "gathering' has somehow produced forty thousand people in the main boulevard. "
            "Their banners are not subtle. Their speaker — a former army officer "
            "named Colonel Heinrich Voss — is receiving something between adoration "
            "and religious fervour from the crowd. "
            "His speech, according to the security services transcript, "
            "contains a significant number of ideas that were last popular "
            "in political contexts that did not end well."
        ),
        "issue_type": "political",
        "urgency": "high",
        "era_years": [(1815, 2060)],
        "ideology_tags": ["Liberal Democracy", "Social Democracy", "Conservative Democracy"],
        "conditions": {"max_stability": 0.55},
        "advisors": [
            {
                "name": "Director-General Sofía Álvarez",
                "role": "Head of State Security",
                "icon": "🔒",
                "option_id": 1,
                "quote": (
                    "Voss's movement has a paramilitary wing. "
                    "They've already attacked two trade union offices. "
                    "Prosecute the violence. Ban the paramilitary units. "
                    "The political party can continue — you cannot ban ideas — "
                    "but the armed gang absolutely can and should be prohibited. "
                    "Do it while we still can."
                ),
            },
            {
                "name": "Justice Minister Aldric Novak",
                "role": "Ministry of Justice",
                "icon": "⚖️",
                "option_id": 2,
                "quote": (
                    "Our constitution allows the prohibition of parties that explicitly "
                    "seek to destroy the constitutional order. Voss is explicit about this — "
                    "I have the transcripts. "
                    "Ban the movement entirely. Act now. "
                    "Every week you wait, he has more followers and more funding. "
                    "The window for this closes."
                ),
            },
            {
                "name": "Chief of Staff Gregor Patel",
                "role": "Chief of Staff",
                "icon": "🗂️",
                "option_id": 3,
                "quote": (
                    "Banning him makes him a martyr and his followers into believers. "
                    "Voss exists because people are frightened and economically insecure "
                    "and looking for something clear and simple to believe in. "
                    "Address the fear. Address the insecurity. "
                    "You don't defeat movements like this in court. "
                    "You make them unnecessary."
                ),
            },
        ],
        "options": [
            {
                "id": 1,
                "text": "Prosecute paramilitary violence; ban the armed wing",
                "effects": {"stability": 0.04, "prestige": 4, "war_support": -0.02},
                "flavor": "The paramilitary units scatter and reform under new names. "
                          "Voss's political movement continues. His lawyers are busy.",
                "news": "Government Bans Nationalist Paramilitaries — Political Movement Continues",
            },
            {
                "id": 2,
                "text": "Ban the entire movement under anti-extremism law",
                "effects": {"stability": 0.02, "prestige": -5, "happiness": 0.02, "war_support": 0.04},
                "flavor": "Voss is arrested. Half the country calls him a martyr. "
                          "Underground cells begin forming within a week.",
                "news": "Nationalist Movement Banned, Leader Arrested — Underground Activity Reported",
            },
            {
                "id": 3,
                "text": "Address root causes — economic security and community investment",
                "effects": {"stability": 0.07, "happiness": 0.05, "gdp_growth": -0.012},
                "flavor": "Voss loses his majority in the next regional vote by a "
                          "comfortable margin. He blames foreign interference. "
                          "He does this from a significant distance.",
                "news": "Government Launches Economic Security Programme to Counter Extremist Appeal",
            },
        ],
    },

    # ════════════════════════════════════════════════════════════
    #  MORE UNIVERSAL ISSUES
    # ════════════════════════════════════════════════════════════

    {
        "id": "u_rural_hospital",
        "title": "The Hospital in Gravenhal Will Close on Friday",
        "description": (
            "The only hospital serving three rural provinces — Gravenhal General, "
            "founded 1891, capacity 220 beds — has announced that it will close "
            "at 11:59pm on Friday due to insufficient government funding. "
            "The next nearest hospital is 140 kilometres away over mountain roads "
            "that are impassable in winter. "
            "The head nurse, Sister Agata Bryngelssen, has been running the hospital "
            "for thirty-one years and issued a statement that reads, in its entirety: "
            "'This is shameful.' She did not elaborate. "
            "She didn't need to."
        ),
        "issue_type": "social",
        "urgency": "high",
        "era_years": [(1815, 2060)],
        "ideology_tags": [],
        "conditions": {},
        "advisors": [
            {
                "name": "Sister Agata Bryngelssen",
                "role": "Head Nurse, Gravenhal General",
                "icon": "🏥",
                "option_id": 1,
                "quote": (
                    "I have delivered over three thousand babies in this building. "
                    "I have set bones, treated fevers, sat with dying people through the night. "
                    "The government is going to close us for want of a budget line. "
                    "I am not asking for much. "
                    "I am asking for the amount of money it costs to keep people alive. "
                    "That used to be considered a reasonable thing to ask for."
                ),
            },
            {
                "name": "Finance Minister Adaeze Okafor",
                "role": "Ministry of Finance",
                "icon": "📊",
                "option_id": 2,
                "quote": (
                    "The hospital is running at 34% capacity and costs five times "
                    "the per-patient rate of the regional facility. "
                    "I understand that 140km is far. "
                    "I also understand that we cannot fund every rural institution "
                    "regardless of efficiency. "
                    "An improved transport subsidy for medical travel is cheaper "
                    "and arguably more effective. "
                    "I recognise this is an unpopular thing to say in this room."
                ),
            },
            {
                "name": "Regional MP Tobias Fenn",
                "role": "Member of Parliament, Northern Province",
                "icon": "🗳️",
                "option_id": 3,
                "quote": (
                    "A compromise: fund it as a 'community health hub' — "
                    "urgent care and maternity, no full surgery ward. "
                    "It costs a third of keeping the full hospital open. "
                    "Sister Bryngelssen has already told me she'll run it. "
                    "It's not perfect. It keeps people from dying on a mountain road."
                ),
            },
        ],
        "options": [
            {
                "id": 1,
                "text": "Full emergency funding — keep Gravenhal General open",
                "effects": {"happiness": 0.06, "stability": 0.04, "gdp_growth": -0.007},
                "flavor": "The hospital stays open. Sister Bryngelssen does not issue "
                          "a statement because she is already back at work.",
                "news": "Gravenhal Hospital Saved by Emergency Government Funding",
            },
            {
                "id": 2,
                "text": "Let it close; fund better medical transport for rural patients",
                "effects": {"happiness": -0.06, "stability": -0.04, "gdp_growth": -0.002},
                "flavor": "Two people die on the mountain road in the first winter. "
                          "The transport subsidy is revised.",
                "news": "Rural Hospital Closes — Government Promises Transport Subsidies",
            },
            {
                "id": 3,
                "text": "Convert to a community health hub — urgent care and maternity only",
                "effects": {"happiness": 0.02, "stability": 0.02, "gdp_growth": -0.003},
                "flavor": "The hub opens the following Monday. Sister Bryngelssen runs it "
                          "with evident controlled frustration at having fewer resources "
                          "than she deserves.",
                "news": "Gravenhal Hospital Saved as Community Health Hub — Full Service Reduced",
            },
        ],
    },

    {
        "id": "u_pollution",
        "title": "The River is an Interesting Colour",
        "description": (
            "The Avel River, which provides drinking water to three major cities, "
            "has turned a striking shade of orange following an industrial discharge "
            "from a nearby chemical plant. "
            "The plant is owned by Brüder Chemicals AG, whose managing director "
            "has described the discharge as 'a minor anomaly in an otherwise "
            "exemplary environmental record', which is technically accurate "
            "in the sense that nothing this visible has happened before. "
            "Downstream residents are boiling their water. "
            "The fish are not."
        ),
        "issue_type": "social",
        "urgency": "high",
        "era_years": [(1815, 2060)],
        "ideology_tags": [],
        "conditions": {},
        "advisors": [
            {
                "name": "Environmental Inspector Jana Bauer",
                "role": "National Environment Agency",
                "icon": "🌿",
                "option_id": 1,
                "quote": (
                    "The discharge contains chromium, cadmium, and three compounds "
                    "I am still waiting on the laboratory analysis for. "
                    "Shut the plant. Fine them at the maximum available rate. "
                    "Make the company pay for full remediation of the river and "
                    "compensation to downstream residents. "
                    "Then we discuss whether they ever reopen."
                ),
            },
            {
                "name": "Managing Director Klaus Brüder",
                "role": "Brüder Chemicals AG",
                "icon": "🏭",
                "option_id": 2,
                "quote": (
                    "We employ 4,200 people at this facility. "
                    "Shutting us down doesn't clean the river — it just closes the factory. "
                    "We have already committed to a full technical review. "
                    "A proportionate fine and a mandatory improvement programme "
                    "allows us to fix the problem while keeping people employed. "
                    "Also the orange colour dissipates naturally. I have been told."
                ),
            },
            {
                "name": "Downstream Residents' Committee",
                "role": "River Avel Community Coalition",
                "icon": "💧",
                "option_id": 3,
                "quote": (
                    "My children cannot drink tap water. "
                    "My neighbour's dog is ill. "
                    "The colour is, I admit, interesting, but this is not an art project. "
                    "Whatever you decide about the factory, please — please — "
                    "give us clean water first. "
                    "Everything else is secondary."
                ),
            },
        ],
        "options": [
            {
                "id": 1,
                "text": "Shut the plant; maximum fine; mandatory full remediation",
                "effects": {"stability": 0.03, "prestige": 6, "happiness": 0.05, "gdp_growth": -0.006, "unemployment": 0.01},
                "flavor": "The plant closes. The river gradually returns to a less alarming colour. "
                          "4,200 people are unemployed. The river is cleaner.",
                "news": "Chemical Plant Shut After River Pollution — Remediation Ordered",
            },
            {
                "id": 2,
                "text": "Fine the company; require mandatory improvement programme",
                "effects": {"stability": -0.02, "prestige": -3, "happiness": -0.02, "gdp_growth": -0.002},
                "flavor": "The improvement programme is 'ongoing'. The river is 'recovering'. "
                          "The downstream residents continue to boil their water.",
                "news": "Chemical Company Fined for River Pollution — Improvement Plan Required",
            },
            {
                "id": 3,
                "text": "Emergency clean water supply; investigate plant; decide later",
                "effects": {"stability": 0.01, "happiness": 0.02, "prestige": 0},
                "flavor": "Water tankers arrive within 48 hours. The investigation begins. "
                          "Brüder's lawyers begin preparing arguments about 'natural orange minerals'.",
                "news": "Emergency Water Supplies Deployed — Pollution Investigation Launched",
            },
        ],
    },

]


# ── Lookup helpers ─────────────────────────────────────────────────────────────

def _check_conditions(issue: dict, at_war: bool, game_context: dict) -> bool:
    """Return True if the issue's conditions are met by the current game state."""
    cond = issue.get("conditions", {})
    if not cond:
        return True

    gc = game_context or {}

    if "at_war" in cond and cond["at_war"] != at_war:
        return False
    if "min_stability" in cond and gc.get("stability", 1.0) < cond["min_stability"]:
        return False
    if "max_stability" in cond and gc.get("stability", 1.0) > cond["max_stability"]:
        return False
    if "min_unemployment" in cond and gc.get("unemployment", 0.0) < cond["min_unemployment"]:
        return False
    if "max_unemployment" in cond and gc.get("unemployment", 0.0) > cond["max_unemployment"]:
        return False
    if "min_world_tension" in cond and gc.get("world_tension", 0.0) < cond["min_world_tension"]:
        return False
    if "max_world_tension" in cond and gc.get("world_tension", 0.0) > cond["max_world_tension"]:
        return False
    if "min_happiness" in cond and gc.get("happiness", 1.0) < cond["min_happiness"]:
        return False
    if "max_happiness" in cond and gc.get("happiness", 1.0) > cond["max_happiness"]:
        return False
    if "min_gdp_growth" in cond and gc.get("gdp_growth", 0.0) < cond["min_gdp_growth"]:
        return False
    if "max_gdp_growth" in cond and gc.get("gdp_growth", 0.0) > cond["max_gdp_growth"]:
        return False

    return True


def _check_chain(issue: dict, game_context: dict) -> bool:
    """Return True if a chained issue's prerequisite choice has been made."""
    chain = issue.get("chains_from")
    if not chain:
        return True  # not a chain issue — always eligible

    resolved_options = (game_context or {}).get("resolved_options", {})
    required_issue = chain["issue_id"]
    required_option = chain["option_id"]

    chosen = resolved_options.get(required_issue)
    return chosen == required_option


def generate_auto_issue(
    issue_type: str,
    ideology: str = "",
    game_context: Optional[dict] = None,
) -> Optional[dict]:
    """Generate a lightweight issue based on current game context."""
    if game_context is None:
        game_context = {}

    stability = game_context.get("stability", 0.6)
    unemployment = game_context.get("unemployment", 0.08)
    inflation = game_context.get("inflation", 0.03)
    happiness = game_context.get("happiness", 0.6)
    gdp_growth = game_context.get("gdp_growth", 0.02)
    world_tension = game_context.get("world_tension", 0.3)

    if issue_type == "economic":
        urgency = "high" if unemployment > 0.15 or gdp_growth < 0 else "normal"
        title = "Supply Chain Shock Raises Prices"
        desc = (
            "A sudden disruption in shipping has pushed up prices on essential goods. "
            "Businesses demand rapid relief while households cut back on spending."
        )
        options = [
            {"id": 1, "text": "Subsidize logistics and transport firms", "effects": {"gdp_growth": 0.006, "inflation": -0.004, "prestige": 2},
             "flavor": "Cargo moves again, but the treasury takes the hit.",
             "news": "Emergency Transport Subsidies Announced"},
            {"id": 2, "text": "Let markets self-correct; no intervention", "effects": {"gdp_growth": -0.004, "stability": -0.02, "inflation": 0.003},
             "flavor": "Prices settle slowly. Voters do not.",
             "news": "Government Declines to Intervene in Supply Shock"},
            {"id": 3, "text": "Temporary price controls on key goods", "effects": {"stability": 0.02, "gdp_growth": -0.006, "inflation": -0.006},
             "flavor": "Short-term relief, long-term distortions.",
             "news": "Price Controls Imposed on Essential Goods"},
        ]
    elif issue_type == "political":
        urgency = "high" if stability < 0.45 else "normal"
        title = "Cabinet Rift Over Reform Agenda"
        desc = (
            "A public dispute between senior ministers has paralyzed the reform agenda. "
            "The press calls it a crisis of leadership and authority."
        )
        options = [
            {"id": 1, "text": "Broker a compromise and reassign portfolios", "effects": {"stability": 0.04, "prestige": 2},
             "flavor": "A shaky truce buys time.",
             "news": "Cabinet Compromise Reached After Week of Infighting"},
            {"id": 2, "text": "Back one faction and sack the other", "effects": {"stability": -0.03, "prestige": -3, "war_support": 0.02},
             "flavor": "Decisive, but divisive.",
             "news": "Major Cabinet Shakeup Signals New Direction"},
            {"id": 3, "text": "Call for a national address to reset the agenda", "effects": {"stability": 0.02, "prestige": 4},
             "flavor": "The speech helps, for now.",
             "news": "Leader Addresses Nation Amid Cabinet Turmoil"},
        ]
    elif issue_type == "social":
        urgency = "high" if happiness < 0.45 or inflation > 0.08 else "normal"
        title = "Public Protests Over Cost of Living"
        desc = (
            "Demonstrations have erupted in major cities as households struggle with rising costs. "
            "Union leaders are calling for immediate relief."
        )
        options = [
            {"id": 1, "text": "Expand targeted subsidies for low-income households", "effects": {"happiness": 0.04, "gdp_growth": -0.004, "stability": 0.02},
             "flavor": "The streets calm, budgets tighten.",
             "news": "Government Announces Cost-of-Living Relief"},
            {"id": 2, "text": "Crack down on protests to restore order", "effects": {"stability": -0.04, "war_support": 0.03, "prestige": -4},
             "flavor": "Order returns, but resentment grows.",
             "news": "Police Deployed to Disperse Protests"},
            {"id": 3, "text": "Open talks with unions and civic leaders", "effects": {"happiness": 0.02, "stability": 0.02},
             "flavor": "Negotiations cool tempers.",
             "news": "Government Opens Dialogue With Protest Leaders"},
        ]
    elif issue_type == "military":
        urgency = "high" if world_tension > 0.6 else "normal"
        title = "Border Skirmish Sparks Military Debate"
        desc = (
            "A brief skirmish on the frontier has reignited calls for stronger military readiness. "
            "Generals warn that deterrence is slipping."
        )
        options = [
            {"id": 1, "text": "Authorize a limited mobilization", "effects": {"war_support": 0.05, "stability": -0.02},
             "flavor": "Readiness improves, anxiety rises.",
             "news": "Limited Mobilization Ordered After Border Incident"},
            {"id": 2, "text": "Pursue quiet diplomacy to de-escalate", "effects": {"prestige": 4, "war_support": -0.02},
             "flavor": "Tensions ease, hawks grumble.",
             "news": "Backchannel Talks Aim to Defuse Border Tensions"},
            {"id": 3, "text": "Increase patrols without formal mobilization", "effects": {"war_support": 0.02, "stability": 0.01},
             "flavor": "A cautious show of force.",
             "news": "Border Patrols Intensified Following Skirmish"},
        ]
    elif issue_type == "diplomatic":
        urgency = "high" if world_tension > 0.6 else "normal"
        title = "Regional Trade Bloc Extends Invitation"
        desc = (
            "A new regional trade bloc has invited your nation to join. "
            "Supporters promise growth, critics warn of lost sovereignty."
        )
        options = [
            {"id": 1, "text": "Join the bloc and open markets", "effects": {"gdp_growth": 0.006, "stability": -0.01, "prestige": 3},
             "flavor": "Exports rise as critics watch closely.",
             "news": "Nation Joins Regional Trade Bloc"},
            {"id": 2, "text": "Decline the invitation", "effects": {"stability": 0.02, "prestige": -2},
             "flavor": "Autonomy preserved at a cost.",
             "news": "Government Rejects Trade Bloc Proposal"},
            {"id": 3, "text": "Negotiate special terms before committing", "effects": {"prestige": 4, "gdp_growth": 0.003},
             "flavor": "Talks begin; outcomes uncertain.",
             "news": "Talks Open on Conditional Trade Bloc Membership"},
        ]
    else:
        return None

    return {
        "id": f"auto_{issue_type}_{random.randint(1000, 9999)}",
        "title": title,
        "description": desc,
        "issue_type": issue_type,
        "urgency": urgency,
        "era_years": [(1815, 2060)],
        "ideology_tags": [],
        "conditions": {},
        "advisors": [],
        "options": options,
    }


def get_issues_for_context(
    year: int,
    ideology: str = "",
    issue_type: Optional[str] = None,
    at_war: bool = False,
    used_ids: Optional[set] = None,
    count: int = 1,
    game_context: Optional[dict] = None,
) -> list[dict]:
    """
    Return up to `count` issues that fit the current game context.
    Applies era, ideology, type, condition, chain, and used-ID filters.
    """
    if used_ids is None:
        used_ids = set()
    if game_context is None:
        game_context = {}

    candidates = []
    for issue in ISSUES:
        # Already used in this game
        if issue["id"] in used_ids:
            continue
        # Year / era filter
        if not any(s <= year <= e for s, e in issue["era_years"]):
            continue
        # Ideology filter
        ideo_tags = issue.get("ideology_tags", [])
        if ideo_tags and ideology not in ideo_tags:
            continue
        # Issue type filter
        if issue_type and issue["issue_type"] != issue_type:
            continue
        # Stat/condition filter
        if not _check_conditions(issue, at_war, game_context):
            continue
        # Chain prerequisite filter
        if not _check_chain(issue, game_context):
            continue

        candidates.append(issue)

    if not candidates:
        # Relax: ignore used_ids and type filter, keep era + conditions
        candidates = [
            i for i in ISSUES
            if any(s <= year <= e for s, e in i["era_years"])
            and (not i.get("ideology_tags") or ideology in i["ideology_tags"])
            and _check_conditions(i, at_war, game_context)
            and _check_chain(i, game_context)
        ]

    if not candidates:
        # Absolute fallback: just match the era
        candidates = [i for i in ISSUES if any(s <= year <= e for s, e in i["era_years"])]

    if not candidates:
        candidates = list(ISSUES)

    random.shuffle(candidates)
    return candidates[:count]


def format_issue_for_game(raw: dict) -> dict:
    """Convert library issue format to the game's Issue model format."""
    options = []
    for opt in raw["options"]:
        options.append({
            "id": opt["id"],
            "text": opt["text"],
            "effects": opt.get("effects", {}),
            "flavor": opt.get("flavor", ""),
            "news": opt.get("news", ""),
        })

    return {
        "title": raw["title"],
        "description": raw["description"],
        "issue_type": raw["issue_type"],
        "urgency": raw["urgency"],
        "options": options,
        "advisors": raw.get("advisors", []),
        "source_id": raw["id"],
    }
