// Main game controller

let gameState = null;
let gameId = null;
let ws = null;
let selectedNationId = null;
let pendingWarNationId = null;
let aiOnline = false;

// Flag helpers — backed by the comprehensive COUNTRY_DATA from country-data.js
const FLAG_IDEOLOGY_COLORS = {
  'Liberal Democracy': '#3b82f6', 'Social Democracy': '#22c55e',
  'Conservative Democracy': '#f59e0b', 'Socialism': '#ef4444',
  'Communism': '#dc2626', 'Fascism': '#1c1917', 'Monarchy': '#7c3aed',
  'Theocracy': '#059669', 'Technocracy': '#0ea5e9', 'Oligarchy': '#78716c',
};

function getFlagISO2(name) {
  return (COUNTRY_DATA.nameToAlpha2 || {})[name?.toLowerCase()] || null;
}

function getFlagImg(name, cls = 'flag-img', ideology = null) {
  const iso2 = getFlagISO2(name);
  const size = cls === 'flag-img-lg' ? 24 : 18;
  if (iso2) {
    return `<img class="${cls}" src="https://flagcdn.com/w40/${iso2}.png" alt=""
      data-nation="${encodeURIComponent(name || '')}" data-ideology="${encodeURIComponent(ideology || '')}" data-size="${size}"
      onerror="_handleFlagError(this)"
      style="width:${size}px;height:${Math.round(size*0.67)}px;object-fit:cover;border-radius:2px;vertical-align:middle;flex-shrink:0">`;
  }
  return getFlagFallbackHtml(name, ideology, size);
}

function getFlagFallbackHtml(name, ideology, size = 18) {
  const color = ideology ? (FLAG_IDEOLOGY_COLORS[ideology] || '#555') : '#555';
  const initials = (name || '??').split(' ').map(w => w[0]).join('').slice(0,2).toUpperCase();
  return `<span style="display:inline-flex;align-items:center;justify-content:center;width:${size}px;height:${Math.round(size*0.67)}px;background:${color};color:#fff;font-size:${Math.round(size*0.45)}px;font-weight:700;border-radius:2px;vertical-align:middle;flex-shrink:0">${initials}</span>`;
}

function _handleFlagError(img) {
  const name = decodeURIComponent(img.dataset.nation || '');
  const ideology = decodeURIComponent(img.dataset.ideology || '');
  const size = parseInt(img.dataset.size || '18');
  img.outerHTML = getFlagFallbackHtml(name, ideology, size);
}
window._handleFlagError = _handleFlagError;

// ── Init ──────────────────────────────────────────────────────────────

async function initApp() {
  await loadMenuSaves();
  checkAIStatus();
  UI.showScreen('menu-screen');

  document.getElementById('btn-new-game').addEventListener('click', () => UI.showScreen('setup-screen'));
  document.getElementById('btn-load-game').addEventListener('click', showLoadGameModal);
  document.getElementById('btn-back-menu').addEventListener('click', () => UI.showScreen('menu-screen'));
  document.getElementById('btn-start-game').addEventListener('click', startNewGame);

  await populateSetupScreen();

  document.querySelectorAll('.tab-btn[data-tab]').forEach(btn => {
    btn.addEventListener('click', () => {
      const group = btn.closest('[id$="-tabs"]');
      if (group) UI.setTab(group.id, btn.dataset.tab);
    });
  });

  document.querySelectorAll('[data-close-modal]').forEach(btn => {
    btn.addEventListener('click', () => UI.hideModal(btn.dataset.closeModal));
  });

  document.getElementById('btn-research')?.addEventListener('click', (event) => {
    event.preventDefault();
    window.__debugBanner?.('Research click (JS)');
    if (typeof window.openTechTree === 'function') {
      window.openTechTree();
    } else {
      UI.notify('Research UI failed to load.', 'error');
    }
  });

  document.getElementById('btn-end-turn')?.addEventListener('click', endTurn);

  // War modal casus belli watcher
  document.getElementById('war-casus-belli')?.addEventListener('change', updateWarModalNote);
  document.getElementById('btn-confirm-war')?.addEventListener('click', confirmWarDeclaration);

  MapModule.init('map-container', onMapCountryClick);
  window.addEventListener('resize', () => MapModule.resize());

  // Init WarMapModule once map data is ready
  MapModule.onReady(() => {
    const { svg, g, projection, path } = MapModule.getInternals();
    if (window.WarMapModule && svg && g) {
      WarMapModule.init(svg, g, projection, path);
    }
  });
}

async function checkAIStatus() {
  try {
    const status = await API.status();
    const indicator = document.getElementById('ai-status');
    aiOnline = status.ai.status === 'online';
    if (indicator) {
      indicator.textContent = aiOnline ? '● AI Online' : '● AI Offline';
      indicator.style.color = aiOnline ? 'var(--green)' : 'var(--red)';
    }
  } catch (e) {
    const indicator = document.getElementById('ai-status');
    aiOnline = false;
    if (indicator) { indicator.textContent = '● AI Offline'; indicator.style.color = 'var(--red)'; }
  }
}

// ── Setup Screen ──────────────────────────────────────────────────────

async function populateSetupScreen() {
  const erasData = await API.getEras().catch(() => null);
  if (!erasData) return;

  const eraSelect = document.getElementById('era-select');
  erasData.eras.forEach(era => {
    const opt = document.createElement('option');
    opt.value = era.id;
    opt.textContent = era.name;
    opt.dataset.nations = JSON.stringify(era.major_nations);
    eraSelect.appendChild(opt);
  });

  eraSelect.addEventListener('change', () => {
    const opt = eraSelect.selectedOptions[0];
    if (opt?.dataset.nations) populateNationSelect(JSON.parse(opt.dataset.nations));
    const era = erasData.eras.find(e => e.id === eraSelect.value);
    if (era) document.getElementById('era-description').textContent = era.description || '';
  });

  if (eraSelect.options.length > 1) {
    eraSelect.selectedIndex = 1;
    eraSelect.dispatchEvent(new Event('change'));
  }

  document.querySelectorAll('.ideology-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.ideology-btn').forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
    });
  });
  document.querySelector('.ideology-btn')?.classList.add('selected');
}

function populateNationSelect(nations) {
  const sel = document.getElementById('nation-input');
  sel.innerHTML = '';
  const custom = document.createElement('option');
  custom.value = '';
  custom.textContent = '— Type a custom nation —';
  sel.appendChild(custom);
  nations.forEach(n => {
    const opt = document.createElement('option');
    opt.value = n;
    opt.textContent = n;
    sel.appendChild(opt);
  });
  const customInput = document.getElementById('nation-custom');
  sel.addEventListener('change', () => { if (sel.value && customInput) customInput.value = ''; });
}

let _newGameController = null;
let _wgTimerInterval = null;
let _wgStepInterval = null;

function showWorldGenScreen(eraName, playerNation) {
  document.getElementById('wg-era-label').textContent =
    `${eraName}  ·  ${playerNation}`;
  // Reset all steps to pending
  for (let i = 0; i < 6; i++) {
    const s = document.getElementById(`wgs-${i}`);
    s.classList.remove('done', 'active');
    s.querySelector('.wg-step-icon').textContent = '○';
  }
  // Start step animation — each step takes ~15s, covering ~90s total
  let step = 0;
  function advanceStep() {
    if (step > 0) {
      const prev = document.getElementById(`wgs-${step - 1}`);
      prev.classList.remove('active');
      prev.classList.add('done');
      prev.querySelector('.wg-step-icon').textContent = '✓';
    }
    if (step < 6) {
      const cur = document.getElementById(`wgs-${step}`);
      cur.classList.add('active');
      cur.querySelector('.wg-step-icon').textContent = '▶';
      step++;
      // Each step ~15s, last step stays active until response arrives
      if (step < 6) _wgStepInterval = setTimeout(advanceStep, 15000);
    }
  }
  advanceStep();

  // Elapsed timer
  const start = Date.now();
  const timerEl = document.getElementById('wg-timer');
  _wgTimerInterval = setInterval(() => {
    const s = Math.floor((Date.now() - start) / 1000);
    timerEl.textContent = `${s}s elapsed`;
  }, 1000);

  UI.showScreen('worldgen-screen');
}

function hideWorldGenScreen() {
  clearInterval(_wgTimerInterval);
  clearTimeout(_wgStepInterval);
  _wgTimerInterval = null;
  _wgStepInterval = null;
  // Mark all remaining steps done for a clean finish
  for (let i = 0; i < 6; i++) {
    const s = document.getElementById(`wgs-${i}`);
    if (!s.classList.contains('done')) {
      s.classList.remove('active');
      s.classList.add('done');
      s.querySelector('.wg-step-icon').textContent = '✓';
    }
  }
}

async function startNewGame() {
  const eraId = document.getElementById('era-select').value;
  const nationSel = document.getElementById('nation-input').value;
  const nationCustom = document.getElementById('nation-custom').value.trim();
  const playerNation = nationCustom || nationSel;
  const ideologyBtn = document.querySelector('.ideology-btn.selected');
  const ideology = ideologyBtn?.dataset.ideology || 'Liberal Democracy';

  if (!eraId || !playerNation) { UI.notify('Please select an era and nation.', 'warning'); return; }

  // Cancel any previous in-flight new-game request before starting another
  if (_newGameController) _newGameController.abort();
  _newGameController = new AbortController();
  const signal = _newGameController.signal;

  // Get era name for display
  const eraSelect = document.getElementById('era-select');
  const eraName = eraSelect.options[eraSelect.selectedIndex]?.text || eraId;
  showWorldGenScreen(eraName, playerNation);

  try {
    const result = await API.newGame(eraId, playerNation, ideology, signal);
    hideWorldGenScreen();
    gameId = result.game_id;
    await loadGame(gameId);

    // Show a subtle banner — AI world gen is running in background
    const mapContainer = document.getElementById('map-container');
    if (mapContainer && result.world_ready === false && aiOnline) {
      const banner = document.createElement('div');
      banner.id = 'world-gen-banner';
      banner.style.cssText = [
        'position:absolute', 'top:8px', 'left:50%', 'transform:translateX(-50%)',
        'background:rgba(30,50,80,0.92)', 'border:1px solid #3b82f6',
        'color:#93c5fd', 'padding:6px 14px', 'border-radius:6px',
        'font-size:12px', 'pointer-events:none', 'z-index:50',
        'white-space:nowrap'
      ].join(';');
      banner.textContent = '⏳ AI is generating the world — map will update shortly…';
      mapContainer.style.position = 'relative';
      mapContainer.appendChild(banner);
    }
  } catch (e) {
    hideWorldGenScreen();
    if (e.name === 'AbortError') {
      UI.showScreen('setup-screen');
      return;
    }
    UI.notify(`Failed to start game: ${e.message}`, 'error');
    UI.showScreen('setup-screen');
  } finally {
    _newGameController = null;
    document.getElementById('btn-start-game').disabled = false;
  }
}

function cancelNewGame() {
  if (_newGameController) {
    _newGameController.abort();
    _newGameController = null;
  }
  hideWorldGenScreen();
  UI.showScreen('setup-screen');
  document.getElementById('btn-start-game').disabled = false;
}
window.cancelNewGame = cancelNewGame;

// ── Load / Save ───────────────────────────────────────────────────────

async function loadMenuSaves() {
  const saves = await API.getSaves().catch(() => []);
  const list = document.getElementById('saves-list');
  if (!list) return;
  list.innerHTML = '';
  if (saves.length === 0) {
    list.innerHTML = '<p class="text-dim small italic p-2">No saved games.</p>';
    return;
  }
  saves.forEach(save => {
    const row = document.createElement('div');
    row.className = 'nation-list-item';
    row.innerHTML = `
      <div style="flex:1">
        <div class="bold">${save.player_nation}</div>
        <div class="small text-dim">${save.era_id} · Turn ${save.turn} · ${save.updated_at?.slice(0,10)}</div>
      </div>
      <button class="btn btn-secondary btn-sm" data-id="${save.game_id}">Load</button>
      <button class="btn btn-danger btn-sm delete-save" data-id="${save.game_id}">×</button>
    `;
    row.querySelector('button:not(.delete-save)').addEventListener('click', () => {
      UI.hideModal('load-modal');
      loadGame(save.game_id);
    });
    row.querySelector('.delete-save').addEventListener('click', async (e) => {
      e.stopPropagation();
      await API.deleteGame(save.game_id).catch(() => {});
      row.remove();
    });
    list.appendChild(row);
  });
}

function showLoadGameModal() {
  loadMenuSaves().then(() => UI.showModal('load-modal'));
}

async function loadGame(id) {
  UI.showLoading('Loading game...');
  try {
    gameId = id;
    gameState = await API.getState(id);
    connectWebSocket();
    UI.showScreen('game-screen');
    // Map container had 0 dimensions while hidden — recalculate now that it's visible
    requestAnimationFrame(() => {
      MapModule.resize();
      MapModule.updateColors(gameState);
    });
    renderAll();
  } catch (e) {
    UI.notify(`Load failed: ${e.message}`, 'error');
    UI.showScreen('menu-screen');
  } finally {
    UI.hideLoading();
  }
}

// ── WebSocket ─────────────────────────────────────────────────────────

function connectWebSocket() {
  if (ws) ws.close();
  const wsUrl = `ws://${location.host}/ws/${gameId}`;
  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    setInterval(() => ws.readyState === WebSocket.OPEN && ws.send(JSON.stringify({ type: 'ping' })), 25000);
  };

  ws.onmessage = (evt) => {
    const msg = JSON.parse(evt.data);

    if (msg.type === 'turn_processing') {
      openTurnLog();
      appendTurnLog(msg.message, 'header');
    } else if (msg.type === 'turn_action') {
      appendTurnLog(msg.message, msg.action_type || '');
    } else if (msg.type === 'turn_complete') {
      gameState = msg.state;
      renderAll();
      updateTicker();
      appendTurnLog(`✓ Turn ${gameState.turn} complete — ${UI.monthName(gameState.month)} ${gameState.year}`, 'header');
      document.getElementById('turn-log-title').textContent = `✓ Turn ${gameState.turn} Complete`;
      const spinner = document.getElementById('turn-log-spinner');
      if (spinner) spinner.style.display = 'none';
      document.getElementById('btn-close-turn-log')?.classList.remove('hidden');
    } else if (msg.type === 'issue_resolved') {
      refreshIssues();
    } else if (msg.type === 'world_ready') {
      document.getElementById('world-gen-banner')?.remove();
      // AI world gen finished in the background — update map and nation data
      if (msg.state) {
        gameState = msg.state;
        renderAll();
        updateTicker();
        MapModule.updateColors(gameState);
        UI.notify('World generation complete — AI nations are now active!', 'success');
      } else if (msg.error) {
        UI.notify(`World generation failed: ${msg.error}`, 'warning');
      }
    } else if (msg.type === 'state_update') {
      if (msg.state) {
        gameState = msg.state;
        renderAll();
        updateTicker();
      }
    }
  };

  ws.onerror = () => {};
  ws.onclose = () => {};
}

// ── Turn Log ──────────────────────────────────────────────────────────

function openTurnLog() {
  const modal = document.getElementById('turn-log-modal');
  const content = document.getElementById('turn-log-content');
  const closeBtn = document.getElementById('btn-close-turn-log');
  const title = document.getElementById('turn-log-title');
  const spinner = document.getElementById('turn-log-spinner');
  if (!modal) return;
  content.innerHTML = '';
  closeBtn?.classList.add('hidden');
  title.textContent = 'Processing Turn...';
  if (spinner) spinner.style.display = '';
  modal.classList.remove('hidden');
}

function appendTurnLog(message, type) {
  const content = document.getElementById('turn-log-content');
  if (!content) return;
  const line = document.createElement('div');
  const typeClass = type ? `tl-${type}` : '';
  line.className = `turn-log-line ${typeClass}`;
  line.textContent = message;
  content.appendChild(line);
  content.scrollTop = content.scrollHeight;
}

function closeTurnLog() {
  document.getElementById('turn-log-modal')?.classList.add('hidden');
  document.getElementById('btn-end-turn').disabled = false;
}
window.closeTurnLog = closeTurnLog;

// ── News Ticker ───────────────────────────────────────────────────────

function updateTicker() {
  const el = document.getElementById('ticker-inner');
  if (!el) return;
  const headlines = gameState?.news_feed?.length
    ? gameState.news_feed.slice(0, 10).map(n => `★ ${n.headline}`).join('     ·     ')
    : 'Waiting for world events...';
  // Duplicate for seamless loop (CSS moves by -50%)
  el.textContent = headlines + '     ·     ' + headlines;
  // Restart animation
  el.style.animation = 'none';
  el.offsetHeight; // force reflow
  el.style.animation = '';
}

// ── Render ────────────────────────────────────────────────────────────

function renderAll() {
  if (!gameState) return;
  renderTopBar();
  renderLeftPanel();
  renderRightPanel();
  renderBottomBar();
  MapModule.updateColors(gameState);
  if (selectedNationId) renderNationDetail(selectedNationId);
}

function renderLeftPanel() {
  renderNationPanel();
  renderIssuesPanel();
  renderPoliciesPanel();
  renderMilitaryPanel();  // async — fires independently
}

function renderTopBar() {
  const player = gameState.nations[gameState.player_nation_id];
  if (!player) return;

  const flagEl = document.getElementById('tb-flag');
  if (flagEl) flagEl.innerHTML = getFlagImg(player.name, 'flag-img');

  setText('tb-nation-name', player.name);
  setText('tb-date', `${UI.monthName(gameState.month)} ${gameState.year}`);
  setText('tb-gdp', UI.fmtGDP(player.economy.gdp));
  setText('tb-stability', UI.fmtPct(player.stability));
  setText('tb-prestige', Math.round(player.prestige));
  setText('tb-army', UI.fmtArmy(player.military.army_size));

  const tensionFill = document.getElementById('tension-fill');
  if (tensionFill) tensionFill.style.width = (gameState.world_tension * 100) + '%';
  setText('tension-val', (gameState.world_tension * 100).toFixed(0) + '%');
}

function renderNationPanel() {
  const player = gameState.nations[gameState.player_nation_id];
  if (!player) return;

  const el = document.getElementById('nation-panel-content');
  if (!el) return;

  el.innerHTML = `
    <div class="nation-card">
      <div class="nation-leader-row">
        <div class="leader-avatar">${getFlagImg(player.name, 'flag-img-lg', player.ideology)}</div>
        <div class="nation-name-block">
          <div class="nation-name-big">${player.name}</div>
          <div class="nation-ideology" style="color:${UI.ideologyColor(player.ideology)}">${player.ideology}</div>
          <div class="nation-leader-name">${player.government_type} · ${player.leader || 'Unknown Leader'}</div>
        </div>
        ${(player.controlled_territories || []).length > 0 ? `
          <div class="territory-count-badge" title="Controlled territories">
            🗺 ${player.controlled_territories.length}
          </div>` : ''}
      </div>
      ${UI.statBar('Stability', player.stability, 1, 'fill-green', UI.fmtPct(player.stability))}
      ${UI.statBar('War Support', player.war_support, 1, 'fill-blue', UI.fmtPct(player.war_support))}
      ${UI.statBar('Prestige', player.prestige, 200, 'fill-gold', Math.round(player.prestige))}
    </div>

    <div class="eco-grid mt-2">
      <div class="eco-tile">
        <div class="eco-tile-label">GDP</div>
        <div class="eco-tile-value">${UI.fmtGDP(player.economy.gdp)}</div>
        <div class="eco-tile-sub text-${player.economy.gdp_growth >= 0 ? 'green' : 'red'}">${player.economy.gdp_growth >= 0 ? '+' : ''}${UI.fmtPct(player.economy.gdp_growth)}</div>
      </div>
      <div class="eco-tile">
        <div class="eco-tile-label">Unemployment</div>
        <div class="eco-tile-value">${UI.fmtPct(player.economy.unemployment)}</div>
        <div class="eco-tile-sub text-dim">Inflation ${UI.fmtPct(player.economy.inflation)}</div>
      </div>
      <div class="eco-tile">
        <div class="eco-tile-label">Army</div>
        <div class="eco-tile-value">${UI.fmtArmy(player.military.army_size)}</div>
        <div class="eco-tile-sub text-dim">Morale ${UI.fmtPct(player.military.morale)}</div>
      </div>
      <div class="eco-tile">
        <div class="eco-tile-label">Population</div>
        <div class="eco-tile-value">${UI.fmtArmy(player.population)}</div>
        <div class="eco-tile-sub text-dim">Manpower ${UI.fmtArmy(player.military.manpower_pool)}</div>
      </div>
    </div>

    ${renderNationExtras(player)}
    ${player.is_at_war ? renderActiveWars() : ''}
  `;
}

function renderNationExtras(player) {
  const happiness = player.happiness ?? null;
  const techLevels = player.tech_levels || {};
  const researchPoints = player.research_points ?? 0;
  const researchFocus = player.research_focus || '—';

  let html = '';

  // Happiness bar
  if (happiness !== null) {
    const hapPct = Math.round(happiness * 100);
    const hapColor = happiness >= 0.6 ? 'fill-green' : happiness >= 0.35 ? 'fill-orange' : 'fill-red';
    html += `
      <div class="stat-row mt-2">
        <div class="stat-header">
          <span class="stat-name">Citizen Happiness</span>
          <span class="stat-value">${hapPct}%</span>
        </div>
        <div class="stat-bar">
          <div class="stat-fill ${hapColor}" style="width:${hapPct}%"></div>
        </div>
      </div>`;
  }

  // Tech levels
  if (Object.keys(techLevels).length) {
    const ind = techLevels.industry ?? '?';
    const mil = techLevels.military ?? '?';
    const dip = techLevels.diplomacy ?? '?';
    html += `
      <div class="tech-levels-row mt-2">
        <span class="tech-badge tech-industry">Industry Lv.${ind}</span>
        <span class="tech-badge tech-military">Military Lv.${mil}</span>
        <span class="tech-badge tech-diplomacy">Diplomacy Lv.${dip}</span>
      </div>`;
  }

  // Research progress
  if (player.research_focus !== undefined || player.research_points !== undefined) {
    const rp = Math.min(100, Math.round(researchPoints));
    html += `
      <div class="research-row mt-2">
        <div class="stat-header">
          <span class="stat-name">Research: <span class="text-blue">${researchFocus}</span></span>
          <span class="stat-value">${rp}/100</span>
        </div>
        <div class="stat-bar">
          <div class="stat-fill fill-blue" style="width:${rp}%"></div>
        </div>
      </div>`;
  }

  return html;
}

function renderActiveWars() {
  const playerWars = gameState.active_wars.filter(w =>
    (w.attacker === gameState.player_nation_id || w.defender === gameState.player_nation_id)
    && w.status === 'ongoing'
  );
  if (!playerWars.length) return '';

  return playerWars.map(war => {
    const isAttacker = war.attacker === gameState.player_nation_id;
    const enemyId = isAttacker ? war.defender : war.attacker;
    const enemy = gameState.nations[enemyId];
    const warscore = isAttacker ? war.attacker_warscore : -war.attacker_warscore;
    const wsWidth = Math.min(50, Math.abs(warscore / 2)) + '%';
    const wsClass = warscore >= 0 ? 'attacker' : 'defender';
    const wsColor = warscore >= 0 ? '#22c55e' : '#ef4444';
    const wsSign = warscore >= 0 ? '+' : '';
    const occupiedCount = Object.keys(war.occupied_territories || {}).length;

    // Count active fronts for this war
    const activeFronts = (war.fronts || []).filter(f => f.status === 'active').length;

    return `
      <div class="war-card mt-2">
        <div class="war-header-row">
          <span class="war-title">⚔ ${enemy?.name || enemyId}</span>
          <span class="war-warscore" style="color:${wsColor}">${wsSign}${warscore.toFixed(0)}</span>
        </div>
        <div class="war-meta-row">
          <span class="small text-dim">${war.casus_belli.replace(/_/g, ' ')}</span>
          ${activeFronts > 0 ? `<span class="war-front-count">${activeFronts} front${activeFronts > 1 ? 's' : ''}</span>` : ''}
          ${occupiedCount > 0 ? `<span class="war-occupied-count">🚩${occupiedCount} captured</span>` : ''}
        </div>
        <div class="warscore-track mt-1">
          <div class="warscore-fill ${wsClass}" style="width:${wsWidth}"></div>
          <div class="warscore-center"></div>
        </div>
        <div class="flex" style="justify-content:space-between; font-size:10px; color:var(--text-dim); margin-top:2px">
          <span>Your side</span>
          <span>0</span>
          <span>${enemy?.name || '?'}</span>
        </div>
        <div class="flex gap-2 mt-1">
          <button class="btn btn-secondary btn-sm" onclick="showPeaceModal('${war.id}')">Negotiate Peace</button>
        </div>
      </div>`;
  }).join('');
}

function renderIssuesPanel() {
  const el = document.getElementById('issues-content');
  if (!el) return;

  const activeIssues = gameState.pending_issues.filter(i => !i.resolved);

  if (activeIssues.length === 0) {
    el.innerHTML = `
      <div style="padding:24px 12px; text-align:center; color:var(--text-dim)">
        <div style="font-size:32px;margin-bottom:8px">📋</div>
        <div class="small italic">No pending issues.</div>
        <div class="small" style="margin-top:4px">Advance the turn to see new decisions.</div>
      </div>`;
    return;
  }

  el.innerHTML = activeIssues.map(issue => renderIssueCard(issue)).join('');
}

function renderIssueCard(issue) {
  const advisors = issue.advisors || [];
  // Build advisor map: option_id → advisor
  const advisorMap = {};
  advisors.forEach(a => { advisorMap[a.option_id] = a; });

  const urgencyColors = { critical: '#ef4444', high: '#f59e0b', normal: '#3b82f6', low: '#6b7280' };
  const typeIcons = { economic: '📊', political: '🏛️', social: '👥', military: '⚔️', diplomatic: '🌐' };
  const typeImgs = {
    economic:   '../assets/icon-pieces/Cash.png',
    political:  '../assets/icon-pieces/Treaty.png',
    social:     '../assets/icon-pieces/Scales Golden.png',
    military:   '../assets/icon-pieces/Soldiers Facing.png',
    diplomatic: '../assets/icon-pieces/Global Trade.png',
  };
  const urgencyColor = urgencyColors[issue.urgency] || '#3b82f6';
  const typeEmoji = typeIcons[issue.issue_type] || '📋';
  const typeImg = typeImgs[issue.issue_type];
  const typeIcon = typeImg
    ? `<img src="${typeImg}" style="width:14px;height:14px;object-fit:contain;vertical-align:middle;margin-right:2px" onerror="this.style.display='none'"> ${issue.issue_type}`
    : `${typeEmoji} ${issue.issue_type}`;

  const optionsHtml = issue.options.map(opt => {
    const advisor = advisorMap[opt.id];
    const effectsHtml = renderEffectPills(opt.effects || {});
    return `
      <div class="issue-option-block">
        ${advisor ? `
          <div class="advisor-quote-block">
            <div class="advisor-header">
              <span class="advisor-icon">${advisor.icon || '👤'}</span>
              <div class="advisor-meta">
                <div class="advisor-name">${advisor.name}</div>
                <div class="advisor-role">${advisor.role}</div>
              </div>
            </div>
            <div class="advisor-quote">"${advisor.quote}"</div>
          </div>
        ` : ''}
        <button class="issue-option-btn" onclick="resolveIssue('${issue.id}', ${opt.id})">
          <div class="issue-option-text">${opt.text}</div>
          ${effectsHtml ? `<div class="issue-effects">${effectsHtml}</div>` : ''}
        </button>
      </div>`;
  }).join('');

  return `
    <div class="issue-card-ns" id="issue-${issue.id}">
      <div class="issue-card-header">
        <div class="issue-type-badge">${typeIcon}</div>
        <div class="issue-urgency-badge" style="background:${urgencyColor}20;color:${urgencyColor};border:1px solid ${urgencyColor}40">
          ${issue.urgency.toUpperCase()}
        </div>
      </div>
      <div class="issue-title-ns">${issue.title}</div>
      <div class="issue-description-ns">${issue.description}</div>
      <div class="issue-divider"></div>
      <div class="issue-options-ns">${optionsHtml}</div>
    </div>`;
}

function renderEffectPills(effects) {
  const labels = {
    stability: ['Stability', '#22c55e', '#ef4444'],
    happiness: ['Happiness', '#22c55e', '#ef4444'],
    war_support: ['War Support', '#3b82f6', '#ef4444'],
    prestige: ['Prestige', '#eab308', '#6b7280'],
    gdp_growth: ['GDP Growth', '#22c55e', '#ef4444'],
    unemployment: ['Unemployment', '#ef4444', '#22c55e'],
    research_points: ['Research', '#8b5cf6', '#8b5cf6'],
    world_tension: ['Tension', '#ef4444', '#22c55e'],
  };
  const pills = [];
  for (const [key, val] of Object.entries(effects)) {
    if (!val || key.startsWith('stockpile.') || key === 'tech_boost') continue;
    const meta = labels[key];
    if (!meta) continue;
    const [label, posColor, negColor] = meta;
    const color = val > 0 ? posColor : negColor;
    const sign = val > 0 ? '+' : '';
    const display = Math.abs(val) < 1 ? `${sign}${(val * 100).toFixed(0)}%` : `${sign}${val.toFixed(0)}`;
    pills.push(`<span class="effect-pill" style="background:${color}22;color:${color};border:1px solid ${color}44">${label} ${display}</span>`);
  }
  return pills.join('');
}

function renderRightPanel() {
  renderDiplomacyPanel();
  renderEconomyPanel();
  renderNewsPanel();
}

function renderDiplomacyPanel() {
  const el = document.getElementById('diplomacy-content');
  if (!el) return;

  const player = gameState.nations[gameState.player_nation_id];
  const nations = Object.entries(gameState.nations)
    .filter(([id]) => id !== gameState.player_nation_id)
    .filter(([, n]) => n.is_alive)
    .sort(([, a], [, b]) => (b.economy.gdp - a.economy.gdp));

  el.innerHTML = nations.map(([nid, nation]) => {
    const rel = player?.diplomacy.relations[nid] ?? 0;
    const isAlly = player?.diplomacy.alliances.includes(nid);
    const isAtWar = gameState.active_wars.some(w =>
      (w.attacker === gameState.player_nation_id && w.defender === nid) ||
      (w.defender === gameState.player_nation_id && w.attacker === nid)
    );
    const ideoDot = `<span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${UI.ideologyColor(nation.ideology)};margin-right:4px;flex-shrink:0"></span>`;
    return `
      <div class="nation-list-item" onclick="selectNation('${nid}')">
        ${ideoDot}
        <div style="flex:1; min-width:0">
          <div class="nation-list-name bold">${getFlagImg(nation.name, 'flag-img', nation.ideology)} ${nation.name}
            ${isAlly ? '<span class="small text-gold"> ★</span>' : ''}
            ${isAtWar ? '<span class="small text-red"> ⚔</span>' : ''}
          </div>
          <div class="nation-list-ideology">${nation.ideology} · ${UI.fmtGDP(nation.economy.gdp)}</div>
        </div>
        ${UI.relationBadge(rel)}
      </div>
      ${renderAdvancedDiplomacy(nid)}`;
  }).join('');
}

function renderEconomyPanel() {
  const player = gameState.nations[gameState.player_nation_id];
  if (!player) return;
  const eco = player.economy;
  const overviewEl = document.getElementById('eco-overview-content');
  if (overviewEl) {
    overviewEl.innerHTML = `
      <div class="eco-grid">
        <div class="eco-tile">
          <div class="eco-tile-label">GDP</div>
          <div class="eco-tile-value">${UI.fmtGDP(eco.gdp)}</div>
          <div class="eco-tile-sub text-${eco.gdp_growth >= 0 ? 'green' : 'red'}">${eco.gdp_growth >= 0 ? '+' : ''}${UI.fmtPct(eco.gdp_growth)}</div>
        </div>
        <div class="eco-tile">
          <div class="eco-tile-label">Unemployment</div>
          <div class="eco-tile-value">${UI.fmtPct(eco.unemployment)}</div>
          <div class="eco-tile-sub">Inflation ${UI.fmtPct(eco.inflation)}</div>
        </div>
        <div class="eco-tile">
          <div class="eco-tile-label">Trade Balance</div>
          <div class="eco-tile-value">${eco.trade_balance >= 0 ? '+' : ''}${eco.trade_balance.toFixed(1)}</div>
          <div class="eco-tile-sub">Openness ${UI.fmtPct(eco.trade_openness)}</div>
        </div>
        <div class="eco-tile">
          <div class="eco-tile-label">Industry Output</div>
          <div class="eco-tile-value">${eco.industry_output.toFixed(0)}</div>
          <div class="eco-tile-sub">Factories ${eco.factories}</div>
        </div>
      </div>
      <div class="small text-dim mt-1">Policy effects come from research, diplomacy, alliances, trades, and issues.</div>
    `;
  }

  // Stockpile
  const stockpile = player.economy?.stockpile || {};
  const stockEl = document.getElementById('eco-stockpile-content');
  if (stockEl) {
    stockEl.innerHTML = `
      <div class="stockpile-grid">
        <div class="stockpile-item"><span class="stockpile-label">Steel</span><span class="stockpile-val">${(stockpile.steel ?? 0).toFixed(0)}</span></div>
        <div class="stockpile-item"><span class="stockpile-label">Fuel</span><span class="stockpile-val">${(stockpile.fuel ?? 0).toFixed(0)}</span></div>
        <div class="stockpile-item"><span class="stockpile-label">Equipment</span><span class="stockpile-val">${(stockpile.equipment ?? 0).toFixed(0)}</span></div>
      </div>`;
  }

  // Factories
  const facEl = document.getElementById('eco-factories-content');
  if (facEl) {
    facEl.innerHTML = `
      <div class="factories-row">
        <span class="factory-badge">Factories: <strong>${eco.factories ?? 0}</strong></span>
        <span class="factory-badge">Arms: <strong>${eco.arms_factories ?? 0}</strong></span>
        <span class="factory-badge">Labs: <strong>${eco.research_labs ?? 0}</strong></span>
      </div>`;
  }

  // Active resource trades
  renderActiveTrades();
}

async function renderPoliciesPanel() {
  const container = document.getElementById('policies-content');
  const slotsEl = document.getElementById('policies-slots-bar');
  if (!container || !gameId) return;
  try {
    const data = await API.getPolicies(gameId);
    if (slotsEl) {
      slotsEl.innerHTML = `
        <div class="policy-slots">
          <span class="policy-slots-label">Active Policies</span>
          <span class="policy-slots-count">${data.active_count}/${data.max_active}</span>
          <span class="policy-slots-count">PP ${Math.floor(data.political_power ?? 0)}</span>
        </div>`;
    }
    container.innerHTML = data.policies.map(p => renderPolicyCard(p)).join('');
  } catch (e) {
    container.innerHTML = '<p class="text-dim small p-2">Could not load policies.</p>';
  }
}

const POLICY_CAT_BG = {
  military:    '../assets/idea-bg/Army.png',
  economic:    '../assets/idea-bg/Diamond.png',
  social:      '../assets/idea-bg/Pentagon.png',
  diplomatic:  '../assets/idea-bg/Intrigue.png',
  ideological: '../assets/idea-bg/Shield.png',
};

function renderPolicyCard(policy) {
  const disabled = !policy.available || policy.has_conflict || policy.can_afford === false;
  const classes = [
    'policy-card',
    policy.active ? 'policy-active' : '',
    disabled ? 'policy-disabled' : '',
  ].filter(Boolean).join(' ');
  const status = policy.active ? 'Active' : 'Inactive';
  const reason = policy.unavailable_reason || (policy.has_conflict ? 'Conflicts with active policy' : '');
  const badge = policy.ideology_match ? '<span class="policy-badge">Ideology Fit</span>' : '';
  const btnLabel = policy.active ? 'Deactivate' : 'Activate';
  const costLabel = policy.cost ? `<span class="policy-badge">Cost: ${policy.cost} PP</span>` : '';
  const affordLabel = policy.can_afford === false ? '<span class="policy-reason">Not enough political power</span>' : '';
  const catBg = POLICY_CAT_BG[policy.category] || '';
  const bgStyle = catBg ? `style="background-image:url('${catBg}');background-size:contain;background-repeat:no-repeat;background-position:center"` : '';

  return `
    <div class="${classes}">
      <div class="policy-icon" ${bgStyle}>${policy.icon || '⚙️'}</div>
      <div class="policy-body">
        <div class="policy-header">
          <div class="policy-title">${policy.name}</div>
          <div class="policy-status">${status}</div>
        </div>
        <div class="policy-category">${policy.category}</div>
        <div class="policy-desc">${policy.description}</div>
        <div class="policy-meta">
          ${badge}
          ${costLabel}
          ${reason ? `<span class="policy-reason">${reason}</span>` : ''}
          ${affordLabel}
        </div>
      </div>
      <button class="btn btn-secondary btn-sm" ${disabled ? 'disabled' : ''}
        onclick="togglePolicy('${policy.id}')">${btnLabel}</button>
    </div>`;
}

async function togglePolicy(policyId) {
  UI.showLoading('Updating policy...');
  try {
    const result = await API.togglePolicy(gameId, { policy_id: policyId });
    gameState = await API.getState(gameId);
    renderAll();
    const actionLabel = result.action === 'activated' ? 'Activated' : 'Deactivated';
    UI.notify(`${actionLabel}: ${result.policy_name}`, 'success');
  } catch (e) {
    UI.notify(e.message, 'warning');
  } finally {
    UI.hideLoading();
  }
}
window.togglePolicy = togglePolicy;

// ── Military Panel (HOI4-style) ───────────────────────────────────────

let _armyData = null;  // cached army data from backend

async function renderMilitaryPanel() {
  const player = gameState.nations[gameState.player_nation_id];
  if (!player) return;
  const el = document.getElementById('military-content');
  if (!el) return;

  const mil = player.military;
  const conscLaw = player.conscription_law || 'limited_conscription';
  const conscLabels = {
    volunteer_only: 'Volunteer Only',
    limited_conscription: 'Limited Conscription',
    extensive_conscription: 'Extensive Conscription',
    service_and_supply: 'Service & Supply',
    all_adults_serve: 'All Adults Serve',
  };

  // Fetch army data
  let armies = [], fronts = [], manpowerPool = mil.manpower_pool, manpowerCap = Math.round(player.population * 0.15);
  try {
    const data = await API.getArmies(gameId);
    _armyData = data;
    armies = data.armies || [];
    fronts = data.fronts || [];
    manpowerPool = data.manpower_pool ?? mil.manpower_pool;
    manpowerCap = data.manpower_cap ?? manpowerCap;
  } catch(e) { /* silent */ }

  const mpPct = Math.round((manpowerPool / Math.max(1, manpowerCap)) * 100);

  el.innerHTML = `
    <!-- Overview stats -->
    <div class="mil-overview">
      <div class="mil-stat-row">
        <span class="mil-stat-label">Manpower</span>
        <span class="mil-stat-val">${UI.fmtArmy(manpowerPool)} / ${UI.fmtArmy(manpowerCap)}</span>
      </div>
      <div class="mil-bar"><div class="mil-bar-fill" style="width:${mpPct}%"></div></div>
      <div class="mil-stat-row" style="margin-top:4px">
        <span class="mil-stat-label">Conscription</span>
        <span class="mil-stat-val text-gold">${conscLabels[conscLaw] || conscLaw}</span>
        <button class="btn btn-secondary btn-xs" onclick="openConscriptionModal()">Change</button>
      </div>
      <div class="mil-stat-row">
        <span class="mil-stat-label">Equipment</span>
        <span class="mil-stat-val">${UI.fmtPct(mil.equipment_level)}</span>
        <span class="mil-stat-label">Morale</span>
        <span class="mil-stat-val">${UI.fmtPct(mil.morale)}</span>
      </div>
    </div>

    <!-- War situation summary -->
    ${gameState.active_wars.length ? _renderWarSummary(fronts) : ''}

    <!-- Army groups -->
    <div class="mil-section-header">
      <span>ARMY GROUPS (${armies.length}/10)</span>
      <button class="btn btn-primary btn-xs" onclick="openCreateArmyModal()">+ Recruit</button>
    </div>

    <div id="army-list">
      ${armies.length === 0
        ? '<p class="text-dim small italic p-2">No armies. Click Recruit to create one.</p>'
        : armies.map(a => _renderArmyCard(a)).join('')
      }
    </div>
  `;

  // Refresh war map overlays
  refreshWarMap(armies, fronts);
}

function _renderWarSummary(fronts) {
  if (!fronts || fronts.length === 0) {
    return `<div class="mil-war-status">⚔ At War — No active fronts. Assign armies to attack!</div>`;
  }
  const activeFronts = fronts.filter(f => f.status !== 'abandoned');
  if (activeFronts.length === 0) {
    return `<div class="mil-war-status">⚔ At War — All fronts resolved. Assign more armies!</div>`;
  }
  return `
    <div class="mil-section-header">WAR FRONTS <span class="text-dim small">(${activeFronts.length} active)</span></div>
    <div class="mil-fronts">
      ${activeFronts.map(f => {
        const sectorBadge = f.sector && f.sector !== 'main'
          ? `<span class="mil-front-sector">${f.sector.toUpperCase()}</span>` : '';
        const statusIcon = f.status === 'captured' ? '✓' : '⚔';
        const statusClass = f.status === 'captured' ? 'text-green' : 'text-gold';
        const armyBadge = f.army_count > 0
          ? `<span class="mil-front-armies">${f.army_count}★</span>` : '';
        return `
          <div class="mil-front-row ${f.status === 'captured' ? 'front-captured' : ''}">
            <span class="mil-front-target">→ ${f.defender_name || f.target_territory}</span>
            ${sectorBadge}
            ${armyBadge}
            <div class="mil-front-bar">
              <div class="mil-front-fill" style="width:${Math.round(f.progress*100)}%"></div>
            </div>
            <span class="mil-front-pct">${Math.round(f.progress*100)}%</span>
            <span class="mil-front-status ${statusClass}">${statusIcon}</span>
          </div>`;
      }).join('')}
    </div>
  `;
}

function _renderArmyCard(army) {
  const tmpl = army.template || {};
  const statusColors = { training: '#f59e0b', ready: '#22c55e', attacking: '#ef4444', defending: '#3b82f6' };
  const statusColor = statusColors[army.status] || '#888';
  const statusLabel = {
    training: `Training (${army.training_progress}/${army.training_turns_required})`,
    ready: 'Ready for Orders',
    attacking: 'Attacking',
    defending: 'Defending',
  }[army.status] || army.status;

  const bgColor = tmpl.color || '#2a3b50';

  const assignedName = army.assigned_target
    ? (gameState.nations[army.assigned_target]?.name || army.assigned_target)
    : '';

  // Find the front this army is on for sector label
  const armyFront = _armyData?.fronts?.find(f => f.id === army.front_id);
  const sectorLabel = armyFront && armyFront.sector !== 'main'
    ? ` [${armyFront.sector.toUpperCase()}]` : '';

  // Order toggle — only show when attacking
  const orderHtml = army.status === 'attacking' ? `
    <div class="army-order-row">
      <span class="army-order-label">Order:</span>
      <div class="army-order-btns">
        <button class="btn btn-xs army-order-btn ${army.order !== 'hold' ? 'order-active' : ''}"
          onclick="setArmyOrder('${army.id}', 'advance')">⚔ Advance</button>
        <button class="btn btn-xs army-order-btn ${army.order === 'hold' ? 'order-active-hold' : ''}"
          onclick="setArmyOrder('${army.id}', 'hold')">🛡 Hold</button>
      </div>
    </div>` : '';

  return `
    <div class="army-card" id="army-card-${army.id}">
      <div class="army-card-header">
        <div class="army-type-badge" style="background:${bgColor}">${tmpl.icon || '??'}</div>
        <div class="army-info">
          <div class="army-name">${army.name}</div>
          <div class="army-sub">${tmpl.name || army.template_id} · ${army.num_divisions} div · ${UI.fmtArmy(army.manpower)} men</div>
        </div>
        <div class="army-status" style="color:${statusColor}">${statusLabel}</div>
      </div>
      ${!army.is_trained ? `
        <div class="army-train-bar">
          <div class="army-train-fill" style="width:${Math.round((army.training_progress/Math.max(1,army.training_turns_required))*100)}%"></div>
        </div>` : `
        <div class="army-health-row">
          <span class="army-health-label">Str</span>
          <div class="army-health-bar"><div class="army-health-fill" style="width:${Math.round(army.strength*100)}%;background:#22c55e"></div></div>
          <span class="army-health-label">Org</span>
          <div class="army-health-bar"><div class="army-health-fill" style="width:${Math.round(army.organization*100)}%;background:#3b82f6"></div></div>
        </div>`}
      ${assignedName ? `<div class="army-target">⚔ Attacking: ${assignedName}${sectorLabel}</div>` : ''}
      ${orderHtml}
      <div class="army-actions">
        ${army.is_trained && army.status !== 'training' ? (
          army.status === 'attacking' ? `
            <button class="btn btn-secondary btn-xs" onclick="openAssignArmyModal('${army.id}')">Redirect</button>
            <button class="btn btn-secondary btn-xs" onclick="recallArmy('${army.id}')">Recall</button>
          ` : `
            <button class="btn btn-danger btn-xs" onclick="openAssignArmyModal('${army.id}')">Attack</button>
          `
        ) : ''}
        <button class="btn btn-secondary btn-xs" onclick="disbandArmy('${army.id}')">Disband</button>
      </div>
    </div>
  `;
}

async function setArmyOrder(armyId, order) {
  try {
    await API.setArmyOrder(gameId, armyId, order);
    gameState = await API.getState(gameId);
    await renderMilitaryPanel();
  } catch(e) {
    UI.notify(`Order failed: ${e.message}`, 'error');
  }
}
window.setArmyOrder = setArmyOrder;

function refreshWarMap(armies, fronts) {
  if (!window.WarMapModule || !gameState) return;
  WarMapModule.update(gameState, armies || [], fronts || []);
}

async function openCreateArmyModal() {
  let templates = [];
  try {
    const data = await API.getArmyTemplates(gameId);
    templates = data.templates || [];
  } catch(e) { UI.notify('Failed to load templates.', 'error'); return; }

  const modal = document.getElementById('create-army-modal');
  if (!modal) return;

  document.getElementById('cam-templates').innerHTML = templates.map(t => `
    <div class="cam-template ${t.id === 'infantry' ? 'selected' : ''}" data-id="${t.id}" onclick="selectArmyTemplate(this, '${t.id}')">
      <div class="cam-template-icon" style="background:${t.color}">${t.icon}</div>
      <div class="cam-template-info">
        <div class="cam-template-name">${t.name}</div>
        <div class="cam-template-desc small text-dim">${t.description}</div>
        <div class="cam-template-stats small">
          ATK ${t.attack} · DEF ${t.defense} · BRK ${t.breakthrough} · ${t.training_turns} turns
        </div>
        <div class="cam-template-cost small text-gold">${t.manpower_per_div.toLocaleString()}/div · ${t.equipment_cost} equip</div>
      </div>
    </div>
  `).join('');

  UI.showModal('create-army-modal');
}
window.openCreateArmyModal = openCreateArmyModal;

function selectArmyTemplate(el, templateId) {
  document.querySelectorAll('.cam-template').forEach(t => t.classList.remove('selected'));
  el.classList.add('selected');
}
window.selectArmyTemplate = selectArmyTemplate;

async function confirmCreateArmy() {
  const template_id = document.querySelector('.cam-template.selected')?.dataset.id || 'infantry';
  const name = document.getElementById('cam-name')?.value.trim() || '';
  const num_divisions = parseInt(document.getElementById('cam-divs')?.value || 3);

  UI.hideModal('create-army-modal');
  UI.showLoading('Recruiting army...');
  try {
    const result = await API.createArmy(gameId, { template_id, name, num_divisions });
    UI.notify(result.message || 'Army created!', 'success');
    gameState = await API.getState(gameId);
    await renderMilitaryPanel();
  } catch(e) {
    UI.notify(`Recruit failed: ${e.message}`, 'error');
  } finally {
    UI.hideLoading();
  }
}
window.confirmCreateArmy = confirmCreateArmy;

function openAssignArmyModal(armyId) {
  // Build list of nations at war with player
  const warEnemies = [];
  for (const war of (gameState.active_wars || [])) {
    if (war.status !== 'ongoing') continue;
    if (war.attacker === gameState.player_nation_id) {
      warEnemies.push(war.defender, ...war.defender_allies);
    } else if (war.defender === gameState.player_nation_id) {
      warEnemies.push(war.attacker, ...war.attacker_allies);
    }
  }
  const uniqueEnemies = [...new Set(warEnemies)];

  if (uniqueEnemies.length === 0) {
    UI.notify('You must be at war to assign armies.', 'warning');
    return;
  }

  const modal = document.getElementById('assign-army-modal');
  if (!modal) return;
  document.getElementById('aam-army-id').value = armyId;
  document.getElementById('aam-army-name').textContent =
    _armyData?.armies?.find(a => a.id === armyId)?.name || 'Army';

  // Sector selector
  const sectors = ['main', 'north', 'south', 'east', 'west', 'flank'];
  const sectorEl = document.getElementById('aam-sector-select');
  if (sectorEl) {
    sectorEl.innerHTML = sectors.map(s =>
      `<option value="${s}">${s.charAt(0).toUpperCase() + s.slice(1)} Front</option>`
    ).join('');
    sectorEl.value = 'main';
  }

  // Show existing fronts for this army's current enemies
  const existingFronts = (_armyData?.fronts || []).filter(
    f => uniqueEnemies.includes(f.target_territory) && f.status === 'active'
  );

  const existingHtml = existingFronts.length > 0 ? `
    <div class="aam-section-label">JOIN EXISTING FRONT</div>
    ${existingFronts.map(f => `
      <div class="aam-front-item" onclick="confirmAssignToFront('${armyId}', '${f.target_territory}', '${f.sector}', '${f.id}')">
        <span class="aam-front-sector-badge">${(f.sector || 'MAIN').toUpperCase()}</span>
        <span class="aam-front-name">→ ${f.defender_name || f.target_territory}</span>
        <div class="aam-front-progress-bar"><div style="width:${Math.round(f.progress*100)}%;height:100%;background:#ef4444;border-radius:2px"></div></div>
        <span class="aam-front-pct">${Math.round(f.progress*100)}%</span>
        <span class="aam-front-armies">${f.army_count || 0} armies</span>
      </div>`).join('')}
    <div class="aam-divider">— OR OPEN NEW FRONT —</div>
  ` : '';

  document.getElementById('aam-targets').innerHTML = `
    ${existingHtml}
    <div class="aam-section-label">SELECT TARGET</div>
    ${uniqueEnemies.map(nid => {
      const n = gameState.nations[nid];
      if (!n || !n.is_alive) return '';
      return `
        <div class="aam-target" onclick="confirmAssignArmy('${armyId}', '${nid}')">
          ${getFlagImg(n.name, 'flag-img', n.ideology)} <span>${n.name}</span>
          <span class="small text-dim">${UI.fmtArmy(n.military.army_size)} troops</span>
        </div>`;
    }).join('')}
    <div class="aam-sector-row">
      <label class="small text-dim">Sector:</label>
      <select id="aam-sector-select" class="aam-sector-sel">
        ${sectors.map(s => `<option value="${s}">${s.charAt(0).toUpperCase() + s.slice(1)} Front</option>`).join('')}
      </select>
      <label class="small text-dim" style="margin-left:8px">
        <input type="checkbox" id="aam-new-front-cb"> New front
      </label>
    </div>
  `;

  UI.showModal('assign-army-modal');
}
window.openAssignArmyModal = openAssignArmyModal;

async function confirmAssignArmy(armyId, targetId) {
  const sector = document.getElementById('aam-sector-select')?.value || 'main';
  const openNew = document.getElementById('aam-new-front-cb')?.checked || false;
  UI.hideModal('assign-army-modal');
  UI.showLoading('Assigning army...');
  try {
    const result = await API.assignArmy(gameId, armyId, targetId, sector, openNew);
    UI.notify(result.message || 'Army assigned!', 'success');
    gameState = await API.getState(gameId);
    await renderMilitaryPanel();
  } catch(e) {
    UI.notify(`Assignment failed: ${e.message}`, 'error');
  } finally {
    UI.hideLoading();
  }
}
window.confirmAssignArmy = confirmAssignArmy;

async function confirmAssignToFront(armyId, targetId, sector, frontId) {
  UI.hideModal('assign-army-modal');
  UI.showLoading('Reinforcing front...');
  try {
    const result = await API.assignArmy(gameId, armyId, targetId, sector, false);
    UI.notify(result.message || 'Army reinforced front!', 'success');
    gameState = await API.getState(gameId);
    await renderMilitaryPanel();
  } catch(e) {
    UI.notify(`Assignment failed: ${e.message}`, 'error');
  } finally {
    UI.hideLoading();
  }
}
window.confirmAssignToFront = confirmAssignToFront;

async function recallArmy(armyId) {
  UI.showLoading('Recalling army...');
  try {
    const result = await API.recallArmy(gameId, armyId);
    UI.notify(result.message || 'Army recalled.', 'success');
    gameState = await API.getState(gameId);
    await renderMilitaryPanel();
  } catch(e) {
    UI.notify(`Recall failed: ${e.message}`, 'error');
  } finally {
    UI.hideLoading();
  }
}
window.recallArmy = recallArmy;

async function disbandArmy(armyId) {
  if (!confirm('Disband this army? Some manpower will be returned.')) return;
  UI.showLoading('Disbanding army...');
  try {
    const result = await API.disbandArmy(gameId, armyId);
    UI.notify(result.message || 'Army disbanded.', 'success');
    gameState = await API.getState(gameId);
    await renderMilitaryPanel();
  } catch(e) {
    UI.notify(`Disband failed: ${e.message}`, 'error');
  } finally {
    UI.hideLoading();
  }
}
window.disbandArmy = disbandArmy;

async function openConscriptionModal() {
  let laws = [];
  try {
    const data = await API.getArmyTemplates(gameId);
    laws = data.conscription_laws || [];
  } catch(e) { return; }

  const player = gameState.nations[gameState.player_nation_id];
  const currentLaw = player?.conscription_law || 'limited_conscription';

  const modal = document.getElementById('conscription-modal');
  if (!modal) return;

  document.getElementById('conscription-laws-list').innerHTML = laws.map(l => `
    <div class="conscription-law-item ${l.id === currentLaw ? 'current' : ''}" onclick="setConscriptionLaw('${l.id}')">
      <div class="cl-header">
        <span class="cl-name">${l.name}</span>
        ${l.id === currentLaw ? '<span class="cl-badge">CURRENT</span>' : `<span class="cl-cost">${l.political_power_cost} PP</span>`}
      </div>
      <div class="cl-desc small text-dim">${l.description}</div>
      <div class="cl-rate small text-gold">${(l.manpower_rate * 100).toFixed(1)}% mobilization rate</div>
    </div>
  `).join('');

  UI.showModal('conscription-modal');
}
window.openConscriptionModal = openConscriptionModal;

async function setConscriptionLaw(lawId) {
  UI.hideModal('conscription-modal');
  UI.showLoading('Changing conscription law...');
  try {
    const result = await API.setConscription(gameId, lawId);
    UI.notify(result.message || 'Conscription law changed.', 'success');
    gameState = await API.getState(gameId);
    await renderMilitaryPanel();
  } catch(e) {
    UI.notify(`Error: ${e.message}`, 'error');
  } finally {
    UI.hideLoading();
  }
}
window.setConscriptionLaw = setConscriptionLaw;

// Army counter click on map — open the assign modal
window.onArmyCounterClick = function(armyId) {
  const army = _armyData?.armies?.find(a => a.id === armyId);
  if (!army) return;
  if (army.status === 'attacking') {
    if (confirm(`Recall ${army.name} from the front?`)) recallArmy(armyId);
  } else if (army.is_trained) {
    openAssignArmyModal(armyId);
  }
};

function renderNewsPanel() {
  const el = document.getElementById('news-content');
  if (!el) return;

  if (!gameState.news_feed?.length) {
    el.innerHTML = '<p class="text-dim small italic p-2">No news yet.</p>';
    return;
  }

  el.innerHTML = gameState.news_feed.slice(0, 20).map(n => `
    <div class="news-item">
      <span class="news-category cat-${n.category}">${n.category}</span>
      <span>${n.headline}</span>
    </div>
  `).join('');
}

async function renderActiveTrades() {
  const el = document.getElementById('active-trades-content');
  if (!el) return;
  try {
    const trades = await API.getResourceTrades(gameId);
    if (!trades || trades.length === 0) {
      el.innerHTML = '<p class="text-dim small italic p-2">No active resource trades.</p>';
      return;
    }
    el.innerHTML = trades.map(t => `
      <div class="trade-item">
        <div class="trade-info">
          <span class="bold small">${t.partner_name || t.target_nation || 'Unknown'}</span>
          <span class="small text-dim"> — Send: ${t.offer_amount} ${t.offer_resource} / Get: ${t.request_amount} ${t.request_resource}</span>
          ${t.turns_remaining !== undefined ? `<span class="small text-dim"> (${t.turns_remaining} turns)</span>` : ''}
        </div>
        <button class="btn btn-danger btn-sm" onclick="cancelTrade('${t.id}')">Cancel</button>
      </div>
    `).join('');
  } catch (e) {
    el.innerHTML = '<p class="text-dim small italic p-2">Could not load trades.</p>';
  }
}

async function cancelTrade(tradeId) {
  try {
    await API.cancelResourceTrade(gameId, tradeId);
    UI.notify('Trade cancelled.', 'success');
    renderActiveTrades();
  } catch (e) {
    UI.notify(`Error cancelling trade: ${e.message}`, 'error');
  }
}
window.cancelTrade = cancelTrade;

// ── Advanced Diplomacy ────────────────────────────────────────────────

const TRADE_RESOURCES = ['steel', 'fuel', 'equipment', 'coal', 'iron_ore', 'oil', 'rubber', 'aluminum'];

function getAllianceTierName(tier) {
  if (!tier || tier === 0) return 'None';
  if (tier === 1) return 'Non-Aggression';
  if (tier === 2) return 'Defense Pact';
  return 'Full Alliance';
}

function getPlayerAllianceTier(nationId) {
  const player = gameState.nations[gameState.player_nation_id];
  if (!player) return 0;
  // Check alliance tier from diplomacy data
  const allianceTiers = player.diplomacy?.alliance_tiers || {};
  if (allianceTiers[nationId] !== undefined) return allianceTiers[nationId];
  // Fall back to binary checks
  if (player.diplomacy?.alliances?.includes(nationId)) return 3;
  if (player.diplomacy?.defense_pacts?.includes(nationId)) return 2;
  return 0;
}

function renderAdvancedDiplomacy(nid) {
  const nation = gameState.nations[nid];
  if (!nation) return '';
  const player = gameState.nations[gameState.player_nation_id];
  const isAtWar = gameState.active_wars.some(w =>
    (w.attacker === gameState.player_nation_id && w.defender === nid) ||
    (w.defender === gameState.player_nation_id && w.attacker === nid)
  );
  const war = gameState.active_wars.find(w =>
    (w.attacker === gameState.player_nation_id && w.defender === nid) ||
    (w.defender === gameState.player_nation_id && w.attacker === nid)
  );
  const allianceTier = getPlayerAllianceTier(nid);
  const allianceTierName = getAllianceTierName(allianceTier);
  const nextTier = Math.min(3, allianceTier + 1);

  const resourceOptions = TRADE_RESOURCES.map(r => `<option value="${r}">${r.replace(/_/g, ' ')}</option>`).join('');
  const techBranchOptions = ['industry','military','diplomacy'].map(b => `<option value="${b}">${b}</option>`).join('');

  const warId = war?.id || '';

  return `
    <div class="adv-diplomacy-section" id="adv-dip-${nid}">
      <div class="adv-dip-header" onclick="toggleAdvDip('${nid}')">
        <span class="small text-dim" style="font-size:10px;letter-spacing:1px;text-transform:uppercase">Advanced Diplomacy</span>
        <span class="adv-dip-chevron" id="adv-dip-chevron-${nid}">▶</span>
      </div>
      <div class="adv-dip-body hidden" id="adv-dip-body-${nid}">

        <!-- Resource Trade -->
        <div class="adv-dip-block">
          <div class="adv-dip-label">Resource Trade</div>
          <div class="adv-dip-form">
            <div class="adv-dip-form-row">
              <label class="small text-dim">Offer</label>
              <select class="form-select adv-select" id="rt-offer-res-${nid}">${resourceOptions}</select>
              <input class="form-input adv-num" id="rt-offer-amt-${nid}" type="number" min="1" value="10" placeholder="amount">
            </div>
            <div class="adv-dip-form-row">
              <label class="small text-dim">Request</label>
              <select class="form-select adv-select" id="rt-req-res-${nid}">${resourceOptions}</select>
              <input class="form-input adv-num" id="rt-req-amt-${nid}" type="number" min="1" value="10" placeholder="amount">
            </div>
            <button class="btn btn-secondary btn-sm" onclick="proposeResourceTrade('${nid}')">Propose Trade</button>
          </div>
        </div>

        ${isAtWar ? `
        <!-- Request Troops -->
        <div class="adv-dip-block">
          <div class="adv-dip-label">Request Troops</div>
          <div class="adv-dip-form">
            <div class="adv-dip-form-row">
              <input class="form-input adv-num" id="rt-troops-${nid}" type="number" min="1000" step="1000" value="10000" placeholder="troop count">
            </div>
            <button class="btn btn-secondary btn-sm" onclick="reqTroops('${nid}', '${warId}')">Request</button>
          </div>
        </div>` : ''}

        <!-- Buy Technology -->
        <div class="adv-dip-block">
          <div class="adv-dip-label">Buy Technology</div>
          <div class="adv-dip-form">
            <div class="adv-dip-form-row">
              <select class="form-select adv-select" id="bt-branch-${nid}">${techBranchOptions}</select>
              <input class="form-input adv-num" id="bt-price-${nid}" type="number" min="1" value="50" placeholder="price (GDP%)">
            </div>
            <button class="btn btn-secondary btn-sm" onclick="buyTech('${nid}')">Buy Tech</button>
          </div>
        </div>

        <!-- Joint Research -->
        <div class="adv-dip-block">
          <div class="adv-dip-label">Joint Research</div>
          <div class="adv-dip-form">
            <div class="adv-dip-form-row">
              <select class="form-select adv-select" id="jr-branch-${nid}">${techBranchOptions}</select>
            </div>
            <button class="btn btn-secondary btn-sm" onclick="proposeJointResearch('${nid}')">Propose</button>
          </div>
        </div>

        <!-- Upgrade Alliance -->
        <div class="adv-dip-block">
          <div class="adv-dip-label">Alliance Tier</div>
          <div class="adv-dip-form">
            <span class="alliance-tier-badge tier-${allianceTier}">${allianceTierName}</span>
            ${nextTier <= 3 ? `<button class="btn btn-success btn-sm" onclick="doUpgradeAlliance('${nid}', ${nextTier})">Propose ${getAllianceTierName(nextTier)}</button>` : '<span class="small text-gold">Max tier reached</span>'}
          </div>
        </div>

      </div>
    </div>`;
}

function toggleAdvDip(nid) {
  const body = document.getElementById(`adv-dip-body-${nid}`);
  const chevron = document.getElementById(`adv-dip-chevron-${nid}`);
  if (!body) return;
  const hidden = body.classList.toggle('hidden');
  if (chevron) chevron.textContent = hidden ? '▶' : '▼';
}
window.toggleAdvDip = toggleAdvDip;

async function proposeResourceTrade(nid) {
  const nation = gameState.nations[nid];
  const offerRes = document.getElementById(`rt-offer-res-${nid}`)?.value;
  const offerAmt = parseFloat(document.getElementById(`rt-offer-amt-${nid}`)?.value || 0);
  const reqRes = document.getElementById(`rt-req-res-${nid}`)?.value;
  const reqAmt = parseFloat(document.getElementById(`rt-req-amt-${nid}`)?.value || 0);
  if (!offerRes || !reqRes || !offerAmt || !reqAmt) { UI.notify('Fill in all trade fields.', 'warning'); return; }
  try {
    const result = await API.proposeResourceTrade(gameId, {
      target_nation: nation.name,
      offer_resource: offerRes,
      offer_amount: offerAmt,
      request_resource: reqRes,
      request_amount: reqAmt,
    });
    const accepted = result.accepted ?? true;
    UI.notify(result.message || (accepted ? 'Trade proposed!' : 'Trade declined.'), accepted ? 'success' : 'warning', 6000);
    if (accepted) renderActiveTrades();
  } catch (e) {
    UI.notify(`Trade error: ${e.message}`, 'error');
  }
}
window.proposeResourceTrade = proposeResourceTrade;

async function reqTroops(nid, warId) {
  const nation = gameState.nations[nid];
  const troops = parseInt(document.getElementById(`rt-troops-${nid}`)?.value || 0);
  if (!troops) { UI.notify('Enter troop count.', 'warning'); return; }
  try {
    const result = await API.requestTroops(gameId, { target_nation: nation.name, war_id: warId, troops_requested: troops });
    const accepted = result.accepted ?? true;
    UI.notify(result.message || (accepted ? 'Troops requested!' : 'Request declined.'), accepted ? 'success' : 'warning', 6000);
  } catch (e) {
    UI.notify(`Error: ${e.message}`, 'error');
  }
}
window.reqTroops = reqTroops;

async function buyTech(nid) {
  const nation = gameState.nations[nid];
  const branch = document.getElementById(`bt-branch-${nid}`)?.value;
  const price = parseFloat(document.getElementById(`bt-price-${nid}`)?.value || 0);
  if (!branch || !price) { UI.notify('Fill in all fields.', 'warning'); return; }
  try {
    const result = await API.buyTechnology(gameId, { target_nation: nation.name, tech_branch: branch, price_gdp: price });
    const accepted = result.accepted ?? true;
    UI.notify(result.message || (accepted ? 'Technology purchased!' : 'Purchase declined.'), accepted ? 'success' : 'warning', 6000);
    if (accepted) { gameState = await API.getState(gameId); renderAll(); }
  } catch (e) {
    UI.notify(`Error: ${e.message}`, 'error');
  }
}
window.buyTech = buyTech;

async function proposeJointResearch(nid) {
  const nation = gameState.nations[nid];
  const branch = document.getElementById(`jr-branch-${nid}`)?.value;
  if (!branch) { UI.notify('Select a branch.', 'warning'); return; }
  try {
    const result = await API.jointResearch(gameId, { target_nation: nation.name, tech_branch: branch });
    const accepted = result.accepted ?? true;
    UI.notify(result.message || (accepted ? 'Joint research agreed!' : 'Proposal declined.'), accepted ? 'success' : 'warning', 6000);
  } catch (e) {
    UI.notify(`Error: ${e.message}`, 'error');
  }
}
window.proposeJointResearch = proposeJointResearch;

async function doUpgradeAlliance(nid, targetTier) {
  const nation = gameState.nations[nid];
  try {
    const result = await API.upgradeAlliance(gameId, { target_nation: nation.name, target_tier: targetTier });
    const accepted = result.accepted ?? true;
    UI.notify(result.message || (accepted ? `Alliance upgraded to ${getAllianceTierName(targetTier)}!` : 'Upgrade declined.'), accepted ? 'success' : 'warning', 6000);
    if (accepted) { gameState = await API.getState(gameId); renderAll(); }
  } catch (e) {
    UI.notify(`Error: ${e.message}`, 'error');
  }
}
window.doUpgradeAlliance = doUpgradeAlliance;

function renderBottomBar() {
  setText('bb-turn', `Turn ${gameState.turn}`);
  setText('bb-phase', gameState.phase || 'issues');
}

// ── End Turn ──────────────────────────────────────────────────────────

async function endTurn() {
  const btn = document.getElementById('btn-end-turn');
  if (btn) btn.disabled = true;

  // The turn log modal will show progress via WebSocket turn_action messages.
  // openTurnLog() is called when the WS 'turn_processing' message arrives.
  // As a fallback if WS is not connected, show the loading overlay.
  const wsConnected = ws && ws.readyState === WebSocket.OPEN;
  if (!wsConnected) UI.showLoading('AI is processing the world turn...');

  try {
    const result = await API.advanceTurn(gameId);
    if (result.blocked) {
      UI.notify(result.error, 'warning');
      document.getElementById('turn-log-modal')?.classList.add('hidden');
      if (btn) btn.disabled = false;
      return;
    }
    // If WS is not connected, update state manually and re-enable button
    if (!wsConnected) {
      gameState = await API.getState(gameId);
      renderAll();
      updateTicker();
      UI.notify(`Turn ${gameState.turn} complete — ${UI.monthName(gameState.month)} ${gameState.year}`, 'success');
      if (btn) btn.disabled = false;
    }
    // If WS IS connected, turn_complete message handles rendering and the
    // close button re-enables the End Turn button via closeTurnLog().
  } catch (e) {
    UI.notify(`Turn error: ${e.message}`, 'error');
    document.getElementById('turn-log-modal')?.classList.add('hidden');
    if (btn) btn.disabled = false;
  } finally {
    if (!wsConnected) UI.hideLoading();
  }
}

// ── Issues ────────────────────────────────────────────────────────────

async function resolveIssue(issueId, optionId) {
  UI.showLoading('Implementing policy...');
  try {
    const result = await API.respondToIssue(gameId, issueId, optionId);
    gameState = result.state;
    renderAll();
    UI.notify(result.result || 'Policy implemented.', 'success', 5000);
  } catch (e) {
    UI.notify(`Error: ${e.message}`, 'error');
  } finally {
    UI.hideLoading();
  }
}

async function refreshIssues() {
  try {
    gameState = await API.getState(gameId);
    renderAll();
  } catch (e) {}
}

// ── Map & Nation Selection ────────────────────────────────────────────

function onMapCountryClick(nationId, nation) {
  if (!nation) return;
  window.__debugBanner?.(`Map click: ${nation.name || nationId}`);
  selectedNationId = nationId;
  MapModule.highlightNation(nationId);
  openNationModal(nationId);
}

function selectNation(nationId) {
  selectedNationId = nationId;
  MapModule.highlightNation(nationId);
  openNationModal(nationId);
}

function openNationModal(nationId) {
  const nation = gameState.nations[nationId];
  if (!nation) return;

  const player = gameState.nations[gameState.player_nation_id];
  const rel = player?.diplomacy.relations[nationId] ?? 0;
  const isPlayer = nationId === gameState.player_nation_id;
  const isAlly = player?.diplomacy.alliances.includes(nationId);
  const hasTrade = player?.diplomacy.trade_deals.includes(nationId);
  const hasDefPact = player?.diplomacy.defense_pacts.includes(nationId);
  const hasSanctions = player?.diplomacy.sanctions_against.includes(nationId);
  const isAtWar = gameState.active_wars.some(w =>
    (w.attacker === gameState.player_nation_id && w.defender === nationId) ||
    (w.defender === gameState.player_nation_id && w.attacker === nationId)
  );
  const war = gameState.active_wars.find(w =>
    (w.attacker === gameState.player_nation_id && w.defender === nationId) ||
    (w.defender === gameState.player_nation_id && w.attacker === nationId)
  );

  document.getElementById('modal-nation-title').textContent = nation.name;
  document.getElementById('modal-nation-flag').innerHTML = getFlagImg(nation.name, 'flag-img-lg', nation.ideology);

  const body = document.getElementById('modal-nation-body');
  body.innerHTML = `
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:14px">
      <div class="eco-tile">
        <div class="eco-tile-label">Ideology</div>
        <div class="eco-tile-value small bold" style="color:${UI.ideologyColor(nation.ideology)}">${nation.ideology}</div>
      </div>
      <div class="eco-tile">
        <div class="eco-tile-label">Government</div>
        <div class="eco-tile-value small bold">${nation.government_type}</div>
      </div>
      <div class="eco-tile">
        <div class="eco-tile-label">Leader</div>
        <div class="eco-tile-value small">${nation.leader || '—'}</div>
      </div>
      <div class="eco-tile">
        <div class="eco-tile-label">Capital</div>
        <div class="eco-tile-value small">${nation.capital || '—'}</div>
      </div>
    </div>

    ${UI.statBar('Stability', nation.stability, 1, 'fill-green', UI.fmtPct(nation.stability))}
    ${UI.statBar('War Support', nation.war_support, 1, 'fill-blue', UI.fmtPct(nation.war_support))}
    ${!isPlayer ? UI.statBar('Relations', rel + 100, 200, rel >= 0 ? 'fill-green' : 'fill-red', `${rel >= 0 ? '+' : ''}${rel}`) : ''}

    <div class="eco-grid mt-2">
      <div class="eco-tile">
        <div class="eco-tile-label">GDP</div>
        <div class="eco-tile-value">${UI.fmtGDP(nation.economy.gdp)}</div>
        <div class="eco-tile-sub">Growth ${UI.fmtPct(nation.economy.gdp_growth)}</div>
      </div>
      <div class="eco-tile">
        <div class="eco-tile-label">Army</div>
        <div class="eco-tile-value">${UI.fmtArmy(nation.military.army_size)}</div>
        <div class="eco-tile-sub">Equip ${UI.fmtPct(nation.military.equipment_level)}</div>
      </div>
      <div class="eco-tile">
        <div class="eco-tile-label">Population</div>
        <div class="eco-tile-value">${UI.fmtArmy(nation.population)}</div>
        <div class="eco-tile-sub">Prestige ${Math.round(nation.prestige)}</div>
      </div>
      <div class="eco-tile">
        <div class="eco-tile-label">Navy</div>
        <div class="eco-tile-value">${UI.fmtArmy(nation.military.navy_tonnage)}t</div>
        <div class="eco-tile-sub">Air ${nation.military.air_force}</div>
      </div>
    </div>

    ${isAlly ? `<div class="mt-1 text-gold bold small">★ Allied nation</div>` : ''}
    ${hasTrade ? `<div class="mt-1 text-green small">↔ Trade agreement active</div>` : ''}
    ${hasDefPact ? `<div class="mt-1 text-blue small">🛡 Defense pact active</div>` : ''}
    ${hasSanctions ? `<div class="mt-1 text-red small">⛔ You are sanctioning this nation</div>` : ''}
    ${isAtWar ? `<div class="mt-1 text-red bold">⚔ At war with you</div>` : ''}
    ${nation.personality?.historical_grievances?.length ? `
      <div class="mt-2 small text-dim">
        <span class="bold">Grievances:</span> ${nation.personality.historical_grievances.slice(0,3).join(', ')}
      </div>` : ''}
    ${!isPlayer ? renderAdvancedDiplomacy(nationId) : ''}
  `;

  const actions = document.getElementById('modal-nation-actions');
  actions.innerHTML = '';

  if (!isPlayer) {
    if (!isAtWar) {
      actions.innerHTML += `<button class="btn btn-secondary btn-sm" onclick="diplomacyAction('${nationId}', 'improve_relations')">Improve Relations</button>`;
      if (!isAlly) {
        actions.innerHTML += `<button class="btn btn-success btn-sm" onclick="diplomacyAction('${nationId}', 'form_alliance')">Propose Alliance</button>`;
      }
      if (!hasTrade) {
        actions.innerHTML += `<button class="btn btn-secondary btn-sm" onclick="diplomacyAction('${nationId}', 'trade_deal')">Trade Deal</button>`;
      }
      if (!hasDefPact) {
        actions.innerHTML += `<button class="btn btn-secondary btn-sm" onclick="diplomacyAction('${nationId}', 'defense_pact')">Defense Pact</button>`;
      }
      actions.innerHTML += `<button class="btn btn-danger btn-sm" onclick="openWarModal('${nationId}', '${nation.name}')">Declare War</button>`;
      if (!hasSanctions) {
        actions.innerHTML += `<button class="btn btn-secondary btn-sm" onclick="diplomacyAction('${nationId}', 'impose_sanctions')">Impose Sanctions</button>`;
      } else {
        actions.innerHTML += `<button class="btn btn-secondary btn-sm" onclick="diplomacyAction('${nationId}', 'lift_sanctions')">Lift Sanctions</button>`;
      }
    } else {
      actions.innerHTML += `<button class="btn btn-primary btn-sm" onclick="showPeaceModal('${war?.id}')">Negotiate Peace</button>`;
    }
  }

  UI.showModal('nation-modal');
}

function renderNationDetail(nationId) {
  const modal = document.getElementById('nation-modal');
  if (!modal || modal.classList.contains('hidden')) return;
  openNationModal(nationId);
}

// ── War Declaration ───────────────────────────────────────────────────

function openWarModal(nationId, nationName) {
  pendingWarNationId = nationId;
  document.getElementById('war-modal-text').textContent =
    `You are about to declare war on ${nationName}. Choose your justification:`;

  const player = gameState.nations[gameState.player_nation_id];
  const democraticIdeologies = ['Liberal Democracy', 'Social Democracy', 'Conservative Democracy'];
  const noteEl = document.getElementById('war-democracy-note');
  if (democraticIdeologies.includes(player?.ideology) && gameState.world_tension < 0.40) {
    noteEl.textContent = `Warning: As a ${player.ideology}, unprovoked wars require world tension ≥40% (now ${(gameState.world_tension*100).toFixed(0)}%). Choose "Retaliation" or "Defensive War" to bypass.`;
    noteEl.classList.remove('hidden');
  } else {
    noteEl.classList.add('hidden');
  }

  UI.hideModal('nation-modal');
  UI.showModal('war-modal');
}

async function confirmWarDeclaration() {
  const casusBelli = document.getElementById('war-casus-belli')?.value || 'territorial_dispute';
  const nation = gameState.nations[pendingWarNationId];
  if (!nation) return;

  UI.hideModal('war-modal');
  UI.showLoading('Declaring war...');
  try {
    const result = await API.declareWar(gameId, nation.name, casusBelli);
    gameState = await API.getState(gameId);
    renderAll();
    updateTicker();
    UI.notify(result.message || `War declared on ${nation.name}!`, 'error', 6000);
  } catch (e) {
    UI.notify(`War declaration failed: ${e.message}`, 'error', 8000);
  } finally {
    UI.hideLoading();
    pendingWarNationId = null;
  }
}

function updateWarModalNote() {
  // Re-evaluate note if casus belli changes
  const player = gameState?.nations[gameState?.player_nation_id];
  if (!player) return;
  const democraticIdeologies = ['Liberal Democracy', 'Social Democracy', 'Conservative Democracy'];
  const defensiveCasus = ['retaliation', 'defensive_war', 'alliance_defense'];
  const selectedCasus = document.getElementById('war-casus-belli')?.value;
  const noteEl = document.getElementById('war-democracy-note');
  if (!noteEl) return;
  if (democraticIdeologies.includes(player.ideology) &&
      gameState.world_tension < 0.40 &&
      !defensiveCasus.includes(selectedCasus)) {
    noteEl.classList.remove('hidden');
  } else {
    noteEl.classList.add('hidden');
  }
}

// ── Diplomacy ─────────────────────────────────────────────────────────

async function diplomacyAction(nationId, actionType) {
  UI.showLoading('Sending diplomatic message...');
  try {
    const nation = gameState.nations[nationId];
    const result = await API.sendDiplomacy(gameId, actionType, nation.name, {});
    gameState = await API.getState(gameId);
    renderAll();
    const accepted = result.accepted;
    let message = result.response_message || (accepted ? 'Proposal accepted!' : 'Proposal declined.');
    if (!accepted && result.counteroffer) {
      message += ` Counteroffer: ${result.counteroffer}`;
    }
    UI.notify(message, accepted ? 'success' : 'warning', 7000);
    UI.hideModal('nation-modal');
  } catch (e) {
    UI.notify(`Diplomacy error: ${e.message}`, 'error');
  } finally {
    UI.hideLoading();
  }
}

async function showPeaceModal(warId) {
  if (!warId) return;
  UI.showLoading('Generating peace terms...');
  try {
    const terms = await API.getPeaceTerms(gameId, warId);
    const container = document.getElementById('peace-terms-list');
    if (!container) return;

    container.innerHTML = (terms.available_terms || []).map(term => `
      <div class="issue-card" style="margin-bottom:8px">
        <div class="issue-header">
          <div>
            <div class="issue-title">${term.label}</div>
            <div class="small text-dim">Cost: ${term.cost_warscore} warscore</div>
          </div>
        </div>
        <div class="issue-description">${term.description}</div>
        <div class="issue-options">
          <button class="issue-option" onclick="applyPeaceTerm('${warId}', '${term.id}')">
            Apply this term
          </button>
        </div>
      </div>
    `).join('');

    if (terms.flavor_text) {
      container.innerHTML += `<p class="text-dim small italic p-2">${terms.flavor_text}</p>`;
    }

    UI.hideModal('nation-modal');
    UI.showModal('peace-modal');
  } catch (e) {
    UI.notify(`Error: ${e.message}`, 'error');
  } finally {
    UI.hideLoading();
  }
}

async function applyPeaceTerm(warId, termId) {
  UI.showLoading('Applying peace terms...');
  try {
    const result = await API.makePeace(gameId, warId, termId);
    gameState = await API.getState(gameId);
    renderAll();
    updateTicker();
    UI.hideModal('peace-modal');
    UI.notify(result.message || 'Peace established.', 'success', 6000);
  } catch (e) {
    UI.notify(`Peace failed: ${e.message}`, 'error');
  } finally {
    UI.hideLoading();
  }
}

// ── Helpers ───────────────────────────────────────────────────────────

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

// ── Save & Sandbox ────────────────────────────────────────────────────

async function manualSave() {
  const btn = document.getElementById('btn-save-game');
  if (btn) { btn.disabled = true; btn.textContent = '💾 Saving...'; }
  try {
    const result = await API.saveGame(gameId);
    UI.notify(`Game saved — Turn ${result.turn}, ${UI.monthName(result.month)} ${result.year}`, 'success');
  } catch(e) {
    UI.notify(`Save failed: ${e.message}`, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '💾 Save'; }
  }
}
window.manualSave = manualSave;

function openSandbox() {
  const log = document.getElementById('sandbox-log');
  if (log) { log.style.display = 'none'; log.innerHTML = ''; }
  UI.showModal('sandbox-modal');
}
window.openSandbox = openSandbox;

async function sb(action, extras) {
  try {
    const result = await API.sandbox(gameId, action, extras || {});
    const log = document.getElementById('sandbox-log');
    if (log) {
      log.style.display = 'block';
      log.innerHTML += `<div class="sb-log-entry">✓ ${result.messages?.join(' · ') || action}</div>`;
      log.scrollTop = log.scrollHeight;
    }
    // Reload state and refresh UI
    gameState = await API.getState(gameId);
    renderAll();
    // Also refresh military panel since armies/manpower may have changed
    await renderMilitaryPanel();
  } catch(e) {
    const log = document.getElementById('sandbox-log');
    if (log) {
      log.style.display = 'block';
      log.innerHTML += `<div class="sb-log-entry" style="color:#ef4444">✗ ${e.message}</div>`;
    }
    UI.notify(`Sandbox error: ${e.message}`, 'error');
  }
}
window.sb = sb;

// ── Boot ──────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', initApp);

// Expose globals for inline onclick handlers
window.resolveIssue = resolveIssue;
window.selectNation = selectNation;
window.diplomacyAction = diplomacyAction;
window.openWarModal = openWarModal;
window.confirmWarDeclaration = confirmWarDeclaration;
window.showPeaceModal = showPeaceModal;
window.applyPeaceTerm = applyPeaceTerm;
window.endTurn = endTurn;
window.renderNationDetail = renderNationDetail;
window.rendernationaldetail = renderNationDetail;
