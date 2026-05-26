// HoI4-style Tech Tree UI

let _techData = null;
let _activeBranch = 'military';

// Column → branch mapping (matches backend tech_nodes.py)
const COL_BRANCH = {
  0: 'military', 1: 'military', 2: 'military', 3: 'military',
  4: 'industry', 5: 'industry',
  6: 'diplomacy', 7: 'diplomacy',
};

// Branch → display columns
const BRANCH_COLS = {
  military: [0, 1, 2, 3],
  industry: [4, 5],
  diplomacy: [6, 7],
};

// Column headers
const COL_HEADERS = {
  0: 'Infantry',
  1: 'Armour',
  2: 'Air Power',
  3: 'Naval',
  4: 'Industry',
  5: 'Research',
  6: 'Diplomacy',
  7: 'Economy',
};

// Column → idea background image (from AoM shared assets)
const COL_BG = {
  0: '../assets/idea-bg/Army.png',
  1: '../assets/idea-bg/Military Police.png',
  2: '../assets/idea-bg/Airforce.png',
  3: '../assets/idea-bg/Naval.png',
  4: '../assets/idea-bg/Upgrade.png',
  5: '../assets/idea-bg/Modifier.png',
  6: '../assets/idea-bg/Intrigue.png',
  7: '../assets/idea-bg/Diamond.png',
};

// Tech node ID → icon piece PNG (from AoM shared assets icon-pieces/)
const NODE_ICONS = {
  // Infantry
  inf_basic:            '../assets/icon-pieces/Soldiers Facing.png',
  inf_tactics:          '../assets/icon-pieces/Rifles Crossed.png',
  inf_elite:            '../assets/icon-pieces/Soldiers Charging.png',
  inf_motorised:        '../assets/icon-pieces/Soldier Saluting.png',
  inf_swordsmanship:    '../assets/icon-pieces/Soldier.png',
  inf_castle_forts:     '../assets/icon-pieces/Artillery.png',
  inf_bayonet_drill:    '../assets/icon-pieces/Rifle in Hand.png',
  inf_rifled_muskets:   '../assets/icon-pieces/Rifle.png',
  inf_trench_warfare:   '../assets/icon-pieces/Artillery 2.png',
  inf_assault_rifles:   '../assets/icon-pieces/AK47.png',
  inf_mechanized:       '../assets/icon-pieces/Soldiers in Rows.png',
  inf_night_vision:     '../assets/icon-pieces/Soldier Bust.png',
  inf_networked:        '../assets/icon-pieces/Soldiers Saluting.png',
  inf_drone_integration:'../assets/icon-pieces/parachute.png',

  // Armour
  arm_light:            '../assets/icon-pieces/Tank.png',
  arm_medium:           '../assets/icon-pieces/Tank2.png',
  arm_heavy:            '../assets/icon-pieces/Tank3.png',
  arm_blitz:            '../assets/icon-pieces/Tank4.png',
  arm_armored_cars:     '../assets/icon-pieces/Tank5.png',
  arm_tank_destroyers:  '../assets/icon-pieces/Tank Half.png',
  arm_mbt:              '../assets/icon-pieces/Tank on Map.png',
  arm_reactive_armor:   '../assets/icon-pieces/Tank3.png',
  arm_active_protection:'../assets/icon-pieces/Tank4.png',
  arm_autonomous_armor: '../assets/icon-pieces/Tank5.png',

  // Air Power
  air_basic:            '../assets/icon-pieces/Aircraft Fighter.png',
  air_fighters:         '../assets/icon-pieces/Aircraft Fighter Jet.png',
  air_cas:              '../assets/icon-pieces/Aircraft Bomber.png',
  air_strategic:        '../assets/icon-pieces/Bomber.png',
  air_prop_bombers:     '../assets/icon-pieces/Aircraft Bomber2.png',
  air_airlift:          '../assets/icon-pieces/Aircraft Civilian Airliner.png',
  air_jet_fighters:     '../assets/icon-pieces/Aircraft Fighter Jet2.png',
  air_jet_bombers:      '../assets/icon-pieces/Bomber 2.png',
  air_awacs:            '../assets/icon-pieces/Aircraft Fighter2.png',
  air_stealth:          '../assets/icon-pieces/Aircraft Bomber3.png',
  air_drones:           '../assets/icon-pieces/parachute.png',

  // Naval
  nav_basic:            '../assets/icon-pieces/Ship Small.png',
  nav_destroyers:       '../assets/icon-pieces/Ship Medium.png',
  nav_capital:          '../assets/icon-pieces/Ship Large.png',
  nav_carriers:         '../assets/icon-pieces/Ship Large2.png',
  nav_ironclads:        '../assets/icon-pieces/Anchor.png',
  nav_dreadnoughts:     '../assets/icon-pieces/Anchor 2.png',
  nav_submarines:       '../assets/icon-pieces/submarine.png',
  nav_amphibious:       '../assets/icon-pieces/Ship Medium.png',
  nav_nuclear_subs:     '../assets/icon-pieces/Ship Submarine.png',
  nav_missile_cruisers: '../assets/icon-pieces/Missile.png',
  nav_aegis:            '../assets/icon-pieces/Anchor2.png',
  nav_supercarriers:    '../assets/icon-pieces/Ship Large2.png',

  // Industry
  ind_basic:            '../assets/icon-pieces/Cog.png',
  ind_mass:             '../assets/icon-pieces/Cog Wheel.png',
  ind_war_eco:          '../assets/icon-pieces/Cog 2.png',
  ind_synthetic:        '../assets/icon-pieces/Oil Droplet.png',
  ind_canals:           '../assets/icon-pieces/Anchor.png',
  ind_railways:         '../assets/icon-pieces/Cannon.png',
  ind_electrification:  '../assets/icon-pieces/Steel.png',
  ind_oil_refining:     '../assets/icon-pieces/Coal.png',
  ind_automation:       '../assets/icon-pieces/Cog 2.png',
  ind_microelectronics: '../assets/icon-pieces/Beaker Shared.png',
  ind_composites:       '../assets/icon-pieces/Steel.png',
  ind_green_energy:     '../assets/icon-pieces/Scales Golden.png',
  ind_space_industry:   '../assets/icon-pieces/Nuclear Atom 2.png',

  // Research
  res_labs:             '../assets/icon-pieces/Beaker.png',
  res_applied:          '../assets/icon-pieces/Beakers 3.png',
  res_atomic:           '../assets/icon-pieces/Nuclear Atom.png',
  res_computing:        '../assets/icon-pieces/Beaker Shared.png',
  res_radar:            '../assets/icon-pieces/Nuclear Atom 2.png',
  res_rocketry:         '../assets/icon-pieces/Missile.png',
  res_satellites:       '../assets/icon-pieces/Nuclear Cloud.png',
  res_internet:         '../assets/icon-pieces/Global Trade.png',
  res_biotech:          '../assets/icon-pieces/Beakers 3.png',
  res_ai:               '../assets/icon-pieces/Beaker Shared.png',
  res_quantum:          '../assets/icon-pieces/Nuclear Atom.png',

  // Diplomacy
  dip_network:          '../assets/icon-pieces/Globe.png',
  dip_trade:            '../assets/icon-pieces/Treaty.png',
  dip_intel:            '../assets/icon-pieces/Global Trade.png',
  dip_propaganda:       '../assets/icon-pieces/paramilitary.png',
  dip_non_aggression:   '../assets/icon-pieces/Treaty.png',
  dip_defense_pacts:    '../assets/icon-pieces/guns.png',
  dip_alliance_blocs:   '../assets/icon-pieces/Rifles Crossed2.png',
  dip_sanctions_regime: '../assets/icon-pieces/Scales.png',
  dip_peacekeeping:     '../assets/icon-pieces/Globe.png',
  dip_backchannel:      '../assets/icon-pieces/Fist with Cash.png',
  dip_cyber_influence:  '../assets/icon-pieces/Global Trade.png',

  // Economy
  eco_banking:          '../assets/icon-pieces/Bank.png',
  eco_welfare:          '../assets/icon-pieces/Scales Golden.png',
  eco_keynesian:        '../assets/icon-pieces/Cash.png',
  eco_globalisation:    '../assets/icon-pieces/Gold.png',
  eco_tariffs:          '../assets/icon-pieces/Scales.png',
  eco_austerity_policy: '../assets/icon-pieces/Cash Flow Positive.png',
  eco_mega_projects:    '../assets/icon-pieces/Cog Wheel.png',
  eco_global_finance:   '../assets/icon-pieces/Cash2.png',
  eco_supply_chain:     '../assets/icon-pieces/Cash Fan.png',
  eco_digital_currency: '../assets/icon-pieces/Gold.png',
  eco_carbon_markets:   '../assets/icon-pieces/Scales Golden.png',
  eco_mixed_economy:    '../assets/icon-pieces/Bank.png',
};

async function openTechTree() {
  UI.showModal('tech-modal');
  if (!gameId) {
    const c = document.getElementById('tech-tree-container');
    if (c) c.innerHTML = '<p class="text-dim small p-2">Start or load a game to view the tech tree.</p>';
    UI.notify('Game not ready yet. Start or load a campaign.', 'warning');
    return;
  }
  await refreshTechTree();

  // Branch tab listeners (attach once)
  document.querySelectorAll('.tech-branch-btn').forEach(btn => {
    btn.onclick = () => {
      document.querySelectorAll('.tech-branch-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      _activeBranch = btn.dataset.branch;
      renderTechTree();
    };
  });
}
window.openTechTree = openTechTree;

async function refreshTechTree() {
  try {
    const res = await fetch(`/api/game/${gameId}/tech-tree`);
    _techData = await res.json();
    const rpEl = document.getElementById('tech-rp-display');
    if (rpEl) rpEl.textContent = `⚗️ ${Math.floor(_techData.research_points)} RP available`;
    renderTechSlots();
    renderTechTree();
  } catch (e) {
    const c = document.getElementById('tech-tree-container');
    if (c) c.innerHTML = '<p class="text-dim small p-2">Failed to load tech tree.</p>';
    UI.notify('Failed to load tech tree data.', 'error');
  }
}

function renderTechSlots() {
  const bar = document.getElementById('tech-slots-bar');
  if (!bar || !_techData) return;
  const slots = _techData.slots_unlocked || 0;
  const projects = _techData.projects || [];
  const bySlot = {};
  projects.forEach(p => { bySlot[p.slot] = p; });

  const slotHtml = [];
  for (let i = 0; i < slots; i++) {
    const p = bySlot[i];
    const label = p ? `Slot ${i + 1}: ${p.node_id}` : `Slot ${i + 1}: Idle`;
    const progress = p ? `${Math.min(100, Math.floor((p.progress_days / p.total_days) * 100))}%` : '';
    const cls = p ? 'tech-slot active' : 'tech-slot';
    const cancelBtn = p ? `<button class="btn btn-danger btn-sm" onclick="cancelResearch(${i})">×</button>` : '';
    slotHtml.push(`
      <div class="${cls}">
        <span class="tech-slot-name">${label}</span>
        ${progress ? `<span class="tech-slot-progress">${progress}</span>` : ''}
        ${cancelBtn}
      </div>`);
  }
  bar.innerHTML = slotHtml.join('');
}

function renderTechTree() {
  const container = document.getElementById('tech-tree-container');
  if (!container || !_techData) return;

  const cols = BRANCH_COLS[_activeBranch] || [0];
  const nodes = _techData.nodes.filter(n => cols.includes(n.column));

  // Group by column
  const byCol = {};
  cols.forEach(c => { byCol[c] = []; });
  nodes.forEach(n => {
    if (!byCol[n.column]) byCol[n.column] = [];
    byCol[n.column].push(n);
  });
  // Sort each column by row
  cols.forEach(c => { byCol[c].sort((a, b) => a.row - b.row); });

  // Build connection lines (SVG overlay) + node grid
  const nodeW = 180;
  const nodeH = 100;
  const colGap = 20;
  const rowGap = 20;
  const colCount = cols.length;
  const maxRows = Math.max(...cols.map(c => byCol[c].length));

  const totalW = colCount * (nodeW + colGap);
  const totalH = maxRows * (nodeH + rowGap) + 40;

  // Position map for each node id
  const positions = {};
  cols.forEach((col, ci) => {
    byCol[col].forEach((node, ri) => {
      positions[node.id] = {
        x: ci * (nodeW + colGap) + colGap / 2,
        y: ri * (nodeH + rowGap) + 40,
      };
    });
  });

  // Build SVG connection lines
  let svgLines = '';
  nodes.forEach(node => {
    const to = positions[node.id];
    if (!to) return;
    (node.requires || []).forEach(reqId => {
      const from = positions[reqId];
      if (!from) return;
      const x1 = from.x + nodeW;
      const y1 = from.y + nodeH / 2;
      const x2 = to.x;
      const y2 = to.y + nodeH / 2;
      const mx = (x1 + x2) / 2;
      const color = node.researched ? '#22c55e' : (node.can_research ? '#c9a84c' : '#3d3d6b');
      svgLines += `<path d="M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}"
        stroke="${color}" stroke-width="2" fill="none" stroke-dasharray="${node.researched ? '0' : '6,3'}"/>`;
    });
  });

  // Build column headers with idea background images
  const headerHtml = cols.map((col, ci) => {
    const bg = COL_BG[col] ? `style="left:${ci * (nodeW + colGap) + colGap / 2}px;width:${nodeW}px;background-image:url('${COL_BG[col]}');background-size:contain;background-repeat:no-repeat;background-position:left center;"` : `style="left:${ci * (nodeW + colGap) + colGap / 2}px;width:${nodeW}px"`;
    return `<div class="tech-col-header" ${bg}><span class="tech-col-label">${COL_HEADERS[col] || ''}</span></div>`;
  }).join('');

  // Build node cards
  const cardsHtml = nodes.map(node => {
    const pos = positions[node.id];
    if (!pos) return '';
    let cls = 'tech-node';
    if (node.researched) cls += ' tech-researched';
    else if (node.in_progress) cls += ' tech-available';
    else if (node.can_research) cls += ' tech-available';
    else cls += ' tech-locked';

    const costLabel = node.researched ? '✓ Researched' : `${node.days} days`;
    const costColor = node.researched ? '#22c55e' : (node.can_research ? '#c9a84c' : '#5a5a80');
    const clickAttr = node.can_research && !node.researched
      ? `onclick="startResearchNode('${node.id}', '${node.name.replace(/'/g, "\\'")}')"`
      : '';

    const pngSrc = NODE_ICONS[node.id];
    const iconHtml = pngSrc
      ? `<img class="tech-node-img" src="${pngSrc}" alt="" onerror="this.style.display='none';this.nextSibling.style.display='inline'">`
        + `<span class="tech-node-emoji" style="display:none">${node.icon}</span>`
      : `<span class="tech-node-emoji">${node.icon}</span>`;

    return `
      <div class="${cls}" style="left:${pos.x}px;top:${pos.y}px;width:${nodeW}px;height:${nodeH}px" ${clickAttr}
           title="${node.blocked_reason || node.description}">
        <div class="tech-node-icon">${iconHtml}</div>
        <div class="tech-node-name">${node.name}</div>
        <div class="tech-node-cost" style="color:${costColor}">${costLabel}</div>
        <div class="tech-node-unlock">${node.unlock_text || ''}</div>
      </div>`;
  }).join('');

  container.innerHTML = `
    <div class="tech-tree-canvas" style="position:relative;width:${totalW}px;min-height:${totalH}px;margin:0 auto">
      ${headerHtml}
      <svg style="position:absolute;top:0;left:0;width:${totalW}px;height:${totalH}px;pointer-events:none">
        ${svgLines}
      </svg>
      ${cardsHtml}
    </div>`;
}

async function startResearchNode(nodeId, nodeName) {
  if (!_techData) return;
  const slots = _techData.slots_unlocked || 0;
  const projects = _techData.projects || [];
  const usedSlots = new Set(projects.map(p => p.slot));
  const freeSlot = [...Array(slots).keys()].find(i => !usedSlots.has(i));
  if (freeSlot === undefined) {
    UI.notify('All research slots are in use.', 'warning');
    return;
  }
  if (!confirm(`Start research: "${nodeName}" in Slot ${freeSlot + 1}?`)) return;
  try {
    await API.startResearch(gameId, { node_id: nodeId, slot: freeSlot });
    UI.notify(`Research started: ${nodeName}`, 'success');
    await refreshTechTree();
  } catch (e) {
    UI.notify(e.message || 'Research failed', 'error');
  }
}
window.startResearchNode = startResearchNode;

async function cancelResearch(slot) {
  try {
    await API.cancelResearch(gameId, { slot });
    UI.notify('Research cancelled.', 'warning');
    await refreshTechTree();
  } catch (e) {
    UI.notify(e.message || 'Cancel failed', 'error');
  }
}
window.cancelResearch = cancelResearch;
