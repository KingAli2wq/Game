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

  // Build column headers
  const headerHtml = cols.map((col, ci) => `
    <div class="tech-col-header" style="left:${ci * (nodeW + colGap) + colGap / 2}px;width:${nodeW}px">
      ${COL_HEADERS[col] || ''}
    </div>`).join('');

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

    return `
      <div class="${cls}" style="left:${pos.x}px;top:${pos.y}px;width:${nodeW}px;height:${nodeH}px" ${clickAttr}
           title="${node.blocked_reason || node.description}">
        <div class="tech-node-icon">${node.icon}</div>
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
