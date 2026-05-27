from pydantic import BaseModel, Field
from typing import Optional
from uuid import uuid4


class ArmyDivision(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    name: str
    nation_id: str
    template_id: str  # infantry, motorized, armor, artillery, special
    num_divisions: int = 3
    manpower: int = 30000
    strength: float = 1.0       # current health 0–1
    organization: float = 0.0   # 0 in training, rises to 1.0 when trained
    training_progress: int = 0  # turns completed
    training_turns_required: int = 3
    is_trained: bool = False
    location: str = ""          # nation_id of territory where stationed
    assigned_target: Optional[str] = None  # nation_id being attacked
    front_id: Optional[str] = None         # specific WarFront.id this army is assigned to
    order: str = "advance"                 # advance | hold
    status: str = "training"    # training | ready | attacking | defending
    created_turn: int = 0


class WarFront(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    war_id: str
    attacker_nation: str
    defender_nation: str
    target_territory: str       # nation_id of territory being attacked
    sector: str = "main"        # main | north | south | east | west | flank
    progress: float = 0.0       # 0.0 = no advance, 1.0 = captured
    status: str = "active"      # active | captured | abandoned


class EconomyStats(BaseModel):
    gdp: float = 100.0
    gdp_growth: float = 0.03
    unemployment: float = 0.07
    inflation: float = 0.02
    trade_balance: float = 0.0
    industry_output: float = 100.0
    tax_rate: float = 0.30
    gov_spending: float = 0.35
    trade_openness: float = 0.5
    nationalization: float = 0.3
    # Raw resource deposits (extraction capacity per turn)
    resources: dict = Field(default_factory=lambda: {
        "coal": 50, "iron_ore": 50, "oil": 30, "rubber": 20,
        "aluminum": 20, "titanium": 10, "uranium": 5, "rare_earth": 5, "food": 60
    })
    # Processed goods stockpile
    stockpile: dict = Field(default_factory=lambda: {
        "steel": 100.0, "fuel": 100.0, "equipment": 50.0
    })
    # Industrial slots
    factories: int = 10
    arms_factories: int = 3
    research_labs: int = 1


class MilitaryStats(BaseModel):
    army_size: int = 100000
    navy_tonnage: int = 50000
    air_force: int = 100
    manpower_pool: int = 1000000
    equipment_level: float = 0.7
    morale: float = 0.8
    military_spending: float = 0.05


class DiplomacyState(BaseModel):
    alliances: list[str] = Field(default_factory=list)
    defense_pacts: list[str] = Field(default_factory=list)
    trade_deals: list[str] = Field(default_factory=list)
    sanctions_against: list[str] = Field(default_factory=list)
    puppets: list[str] = Field(default_factory=list)
    overlord: Optional[str] = None
    relations: dict[str, int] = Field(default_factory=dict)
    # Alliance tier per nation: 1=non-aggression, 2=defense pact, 3=full alliance
    alliance_tier: dict[str, int] = Field(default_factory=dict)
    # Soft-power influence pool (spent on covert actions, swaying neutrals)
    influence_points: float = 0.0


class NationPersonality(BaseModel):
    aggression: float = 0.5
    economic_priority: str = "balanced"
    diplomatic_tendency: str = "neutral"
    historical_grievances: list[str] = Field(default_factory=list)
    core_claims: list[str] = Field(default_factory=list)


class ResearchProject(BaseModel):
    slot: int
    node_id: str
    progress_days: float = 0.0
    total_days: float = 0.0


class Nation(BaseModel):
    id: str
    name: str
    flag_code: str = ""
    capital: str = ""
    leader: str = ""
    ideology: str = "Liberal Democracy"
    government_type: str = "Republic"
    population: int = 10000000
    stability: float = 0.7
    war_support: float = 0.5
    prestige: float = 50.0
    political_power: float = 30.0
    # Citizen happiness — affected by economy, stability, and issue choices
    happiness: float = 0.65
    # Conscription law affects monthly manpower replenishment
    conscription_law: str = "limited_conscription"
    # Technology levels per branch (1–10) + set of researched HoI4-style node IDs
    tech_levels: dict = Field(default_factory=lambda: {
        "industry": 1, "military": 1, "diplomacy": 1, "researched_nodes": []
    })
    # Accumulated research toward next tech level (0–100 per level)
    research_points: float = 0.0
    # Which tech branch is currently being researched
    research_focus: str = "industry"
    # Research slots (HoI4-style)
    research_slots_unlocked: int = 2
    research_slots_max: int = 3
    research_projects: list[ResearchProject] = Field(default_factory=list)
    is_player: bool = False
    is_at_war: bool = False
    is_alive: bool = True
    color: str = "#888888"
    # Rebellion — grows when stability is critically low
    rebel_strength: float = 0.0
    has_rebellion: bool = False
    # Espionage points (accumulate over turns, spent on missions)
    espionage_points: float = 0.0
    economy: EconomyStats = Field(default_factory=EconomyStats)
    military: MilitaryStats = Field(default_factory=MilitaryStats)
    diplomacy: DiplomacyState = Field(default_factory=DiplomacyState)
    personality: NationPersonality = Field(default_factory=NationPersonality)
    controlled_territories: list[str] = Field(default_factory=list)
    active_policies: list[str] = Field(default_factory=list)


class ResourceTradeOffer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    initiator_id: str
    target_id: str
    offer_resource: str    # what the initiator sends each turn
    offer_amount: float
    request_resource: str  # what the initiator receives each turn
    request_amount: float
    turns_remaining: int = 12
    active: bool = True


class War(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    attacker: str
    defender: str
    attacker_allies: list[str] = Field(default_factory=list)
    defender_allies: list[str] = Field(default_factory=list)
    start_turn: int = 0
    casus_belli: str = ""
    attacker_warscore: float = 0.0
    status: str = "ongoing"
    # Troops contributed by allied nations (nation_id -> count)
    contributed_troops: dict[str, int] = Field(default_factory=dict)
    # HOI4-style fronts and territorial control
    fronts: list[WarFront] = Field(default_factory=list)
    # territory_id -> occupying nation_id
    occupied_territories: dict[str, str] = Field(default_factory=dict)


class IssueOption(BaseModel):
    id: int
    text: str
    effects: dict = Field(default_factory=dict)
    flavor: str = ""
    news: str = ""  # headline published when this option is chosen


class Issue(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    title: str
    description: str
    issue_type: str = "political"
    urgency: str = "normal"
    options: list[IssueOption] = Field(default_factory=list)
    # Named advisor characters who voice each option
    advisors: list[dict] = Field(default_factory=list)
    source_id: str = ""  # library issue ID for dedup tracking
    resolved: bool = False
    chosen_option: Optional[int] = None


class NewsHeadline(BaseModel):
    turn: int
    headline: str
    nation: str
    category: str = "politics"


class GameState(BaseModel):
    game_id: str = Field(default_factory=lambda: str(uuid4())[:12])
    turn: int = 0
    year: int = 1936
    month: int = 1
    era_id: str = "1936"
    player_nation_id: str = ""
    nations: dict[str, Nation] = Field(default_factory=dict)
    active_wars: list[War] = Field(default_factory=list)
    pending_issues: list[Issue] = Field(default_factory=list)
    world_tension: float = 0.3
    news_feed: list[NewsHeadline] = Field(default_factory=list)
    turn_log: list[str] = Field(default_factory=list)
    phase: str = "issues"
    # Active resource trades between nations
    resource_trades: list[ResourceTradeOffer] = Field(default_factory=list)
    # HOI4-style player army groups
    player_armies: list[ArmyDivision] = Field(default_factory=list)
    # Issue frequency — counts down turns; issue generated when reaches 0
    turns_until_next_issue: int = 0
    # Espionage missions in progress (list of mission dicts)
    active_spy_missions: list[dict] = Field(default_factory=list)

    def get_player_nation(self) -> Optional[Nation]:
        return self.nations.get(self.player_nation_id)

    def advance_date(self):
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1
        self.turn += 1

    def add_news(self, headline: str, nation: str, category: str = "politics"):
        self.news_feed.insert(0, NewsHeadline(turn=self.turn, headline=headline, nation=nation, category=category))
        if len(self.news_feed) > 50:
            self.news_feed = self.news_feed[:50]


class NewGameRequest(BaseModel):
    era_id: str
    player_nation_name: str
    ideology: str


class DiplomacyAction(BaseModel):
    action_type: str
    target_nation: str
    details: dict = Field(default_factory=dict)


class IssueResponse(BaseModel):
    option_id: int


class DeclareWarRequest(BaseModel):
    target_nation: str
    casus_belli: str = "territorial_dispute"


class ResourceTradeRequest(BaseModel):
    target_nation: str
    offer_resource: str
    offer_amount: float
    request_resource: str
    request_amount: float


class TroopRequest(BaseModel):
    target_nation: str
    war_id: str
    troops_requested: int = 10000


class TechPurchaseRequest(BaseModel):
    target_nation: str
    tech_branch: str   # industry / military / diplomacy
    price_gdp: float = 20.0


class JointResearchRequest(BaseModel):
    target_nation: str
    tech_branch: str


class AllianceUpgradeRequest(BaseModel):
    target_nation: str
    # Target tier: 1=non-aggression, 2=defense pact, 3=full alliance
    target_tier: int


class CreateArmyRequest(BaseModel):
    template_id: str = "infantry"
    name: str = ""
    num_divisions: int = 3


class AssignArmyRequest(BaseModel):
    target_nation_id: str
    sector: str = "main"            # main | north | south | east | west | flank
    open_new_front: bool = False     # force-create a new front even if one for this sector exists


class ConscriptionRequest(BaseModel):
    law_id: str
