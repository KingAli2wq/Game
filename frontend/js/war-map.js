/**
 * WarMapModule — HOI4-style war overlays on the D3 map.
 * Renders: animated war arrows, army unit counters, territory occupation patterns.
 *
 * Depends on MapModule (map.js) being loaded first.
 */
const WarMapModule = (() => {
  // SVG layer groups inserted above map countries
  let warLayer = null;
  let arrowLayer = null;
  let counterLayer = null;
  let svgEl = null;
  let gEl = null;
  let pathFn = null;      // d3 geo path (updated on resize)
  let projFn = null;      // d3 projection

  // Cache of ISO numeric -> [cx, cy] centroids computed from paths
  const _centroids = {};
  // Cache of nation_id -> [cx, cy] (via name -> ISO lookup)
  const _nationCentroids = {};

  // Template display config mirroring backend army_templates.py
  const TEMPLATE_META = {
    infantry:  { icon: 'INF', color: '#4b7a3b', label: 'Infantry' },
    motorized: { icon: 'MOT', color: '#b8950a', label: 'Motorized' },
    armor:     { icon: 'ARM', color: '#b06a2c', label: 'Armor' },
    artillery: { icon: 'ART', color: '#8b2020', label: 'Artillery' },
    special:   { icon: 'SF',  color: '#4a2080', label: 'Special Forces' },
  };

  // ── Init ──────────────────────────────────────────────────────────────────

  /**
   * Call once after MapModule has loaded map data.
   * svgSel: d3 selection of the <svg> element
   * gSel:   d3 selection of the main <g> group containing country paths
   * proj:   d3 projection function
   * pathGen:d3 geoPath generator
   */
  function init(svgSel, gSel, proj, pathGen) {
    svgEl  = svgSel;
    gEl    = gSel;
    projFn = proj;
    pathFn = pathGen;

    // Insert SVG defs (arrow marker, occupation hatch pattern)
    _injectDefs(svgSel);

    // War overlay groups (appended after country paths so they appear on top)
    warLayer     = gSel.append('g').attr('class', 'war-territory-layer').style('pointer-events', 'none');
    arrowLayer   = gSel.append('g').attr('class', 'war-arrow-layer').style('pointer-events', 'none');
    counterLayer = gSel.append('g').attr('class', 'war-counter-layer');
  }

  function _injectDefs(svgSel) {
    // Only inject once
    if (svgSel.select('defs.war-defs').size() > 0) return;
    const defs = svgSel.append('defs').attr('class', 'war-defs');

    // Arrowhead marker for attack arrows
    defs.append('marker')
      .attr('id', 'war-arrow-head')
      .attr('markerWidth', 10).attr('markerHeight', 7)
      .attr('refX', 9).attr('refY', 3.5)
      .attr('orient', 'auto')
      .append('polygon')
      .attr('points', '0 0, 10 3.5, 0 7')
      .attr('fill', '#ef4444')
      .attr('opacity', 0.9);

    // Arrowhead for defensive arrows (blue)
    defs.append('marker')
      .attr('id', 'def-arrow-head')
      .attr('markerWidth', 10).attr('markerHeight', 7)
      .attr('refX', 9).attr('refY', 3.5)
      .attr('orient', 'auto')
      .append('polygon')
      .attr('points', '0 0, 10 3.5, 0 7')
      .attr('fill', '#3b82f6')
      .attr('opacity', 0.9);

    // Hatched occupation pattern (diagonal stripes)
    const occPattern = defs.append('pattern')
      .attr('id', 'occ-hatch')
      .attr('x', 0).attr('y', 0)
      .attr('width', 8).attr('height', 8)
      .attr('patternUnits', 'userSpaceOnUse')
      .attr('patternTransform', 'rotate(45)');
    occPattern.append('line')
      .attr('x1', 0).attr('y1', 0).attr('x2', 0).attr('y2', 8)
      .attr('stroke', 'rgba(239,68,68,0.45)').attr('stroke-width', 3);

    // Front-line progress gradient (used for progress bars rendered as SVG rects)
    const grad = defs.append('linearGradient')
      .attr('id', 'front-progress-grad')
      .attr('x1', '0%').attr('x2', '100%');
    grad.append('stop').attr('offset', '0%').attr('stop-color', '#ef4444').attr('stop-opacity', 0.9);
    grad.append('stop').attr('offset', '100%').attr('stop-color', '#f97316').attr('stop-opacity', 0.9);
  }

  // ── Main update entry point ────────────────────────────────────────────────

  /**
   * Re-render all war overlays based on current game state + player armies.
   * @param {object} gameState   Full game state from backend
   * @param {Array}  armies      Player army objects (from /military/armies)
   * @param {Array}  fronts      War front objects (from /military/war-fronts)
   */
  function update(gameState, armies, fronts) {
    if (!warLayer) return;
    _buildCentroids(gameState);
    _clearLayers();

    const player = gameState.nations[gameState.player_nation_id];
    if (!player) return;

    // Front line visualizations (attacker borders pulsing red)
    _renderFrontLines(gameState);

    // Occupation overlays for captured territories
    _renderOccupation(gameState);

    // War arrows for each active front
    fronts.forEach(front => _renderArrow(front, gameState));

    // Army counters on map (zoom-invariant, compact HoI4-style)
    armies.forEach(army => _renderCounter(army, gameState));
  }

  // ── Centroid computation ──────────────────────────────────────────────────

  function _buildCentroids(gameState) {
    if (!pathFn) return;
    // For each country-path element, compute centroid and cache by numeric id
    d3.selectAll('.country-path').each(function(d) {
      if (!d || _centroids[d.id]) return;
      try {
        const c = pathFn.centroid(d);
        if (c && !isNaN(c[0]) && !isNaN(c[1])) {
          _centroids[d.id] = c;
        }
      } catch (e) { /* ignore */ }
    });

    // Build nation_id -> centroid via name->ISO lookup
    if (!gameState) return;
    for (const [nid, nation] of Object.entries(gameState.nations)) {
      if (_nationCentroids[nid]) continue;
      const isoNum = (COUNTRY_DATA.nameToISO || {})[nation.name.toLowerCase()];
      if (isoNum && _centroids[isoNum]) {
        _nationCentroids[nid] = _centroids[isoNum];
      } else {
        // Try partial name match
        for (const [name, num] of Object.entries(COUNTRY_DATA.nameToISO || {})) {
          const nl = nation.name.toLowerCase();
          if (nl.includes(name) || name.includes(nl.split(' ')[0])) {
            if (_centroids[num]) {
              _nationCentroids[nid] = _centroids[num];
              break;
            }
          }
        }
      }
    }
  }

  function _getCentroid(nationId) {
    return _nationCentroids[nationId] || null;
  }

  // ── Territory occupation overlay ──────────────────────────────────────────

  function _renderOccupation(gameState) {
    // Highlight occupied territories with a red hatch overlay
    for (const war of (gameState.active_wars || [])) {
      for (const [territory, occupier] of Object.entries(war.occupied_territories || {})) {
        const nation = gameState.nations[territory];
        if (!nation) continue;
        const isoNum = (COUNTRY_DATA.nameToISO || {})[nation.name.toLowerCase()];
        if (!isoNum) continue;

        // Re-use the country-path geometry, just overlay with occupation fill
        const pathEl = d3.select(`#country-${isoNum}`);
        if (!pathEl.empty()) {
          const d = pathEl.datum();
          if (d) {
            warLayer.append('path')
              .attr('d', pathFn(d))
              .attr('fill', 'url(#occ-hatch)')
              .attr('stroke', '#ef4444')
              .attr('stroke-width', 1.5)
              .attr('opacity', 0.7)
              .attr('class', 'occupation-overlay');
          }
        }
      }
    }
  }

  // ── War arrows ────────────────────────────────────────────────────────────

  function _renderArrow(front, gameState) {
    const fromC = _getCentroid(front.attacker_nation);
    const toC   = _getCentroid(front.target_territory || front.defender_nation);
    if (!fromC || !toC) return;

    const isPlayerAttacking = front.attacker_nation === gameState.player_nation_id;
    const arrowColor  = isPlayerAttacking ? '#ef4444' : '#3b82f6';
    const markerId    = isPlayerAttacking ? 'war-arrow-head' : 'def-arrow-head';

    // Offset arrows per sector so multiple fronts don't overlap
    const sectorOffsets = { main: 0, north: -20, south: 20, east: 15, west: -15, flank: 25 };
    const sOff = sectorOffsets[front.sector || 'main'] || 0;

    const dx = toC[0] - fromC[0];
    const dy = toC[1] - fromC[1];
    const len = Math.sqrt(dx * dx + dy * dy) || 1;
    const bulge = Math.min(len * 0.25, 60) + sOff;
    const cx = (fromC[0] + toC[0]) / 2 - (dy / len) * bulge;
    const cy = (fromC[1] + toC[1]) / 2 + (dx / len) * bulge;

    const shrink = 12 / len;
    const ex = toC[0] - dx * shrink;
    const ey = toC[1] - dy * shrink;

    const arrowPath = `M ${fromC[0]},${fromC[1]} Q ${cx},${cy} ${ex},${ey}`;

    // Shadow glow
    arrowLayer.append('path')
      .attr('d', arrowPath)
      .attr('fill', 'none')
      .attr('stroke', arrowColor)
      .attr('stroke-width', 6)
      .attr('stroke-opacity', 0.18)
      .attr('stroke-linecap', 'round')
      .attr('class', 'war-arrow-glow');

    // Animated dashed arrow
    arrowLayer.append('path')
      .attr('d', arrowPath)
      .attr('fill', 'none')
      .attr('stroke', arrowColor)
      .attr('stroke-width', front.status === 'captured' ? 1.5 : 2.5)
      .attr('stroke-dasharray', front.status === 'captured' ? '4 6' : '10 5')
      .attr('stroke-opacity', front.status === 'captured' ? 0.4 : 1)
      .attr('stroke-linecap', 'round')
      .attr('marker-end', front.status === 'captured' ? null : `url(#${markerId})`)
      .attr('class', 'war-arrow-march')
      .style('animation', front.status === 'captured' ? 'none' : 'war-march 0.8s linear infinite');

    // Progress + sector label near midpoint of bezier
    const midBx = 0.25 * fromC[0] + 0.5 * cx + 0.25 * toC[0];
    const midBy = 0.25 * fromC[1] + 0.5 * cy + 0.25 * toC[1];
    if (front.status !== 'abandoned') {
      _renderFrontProgress(midBx, midBy, front.progress, arrowColor, front.sector);
    }
  }

  function _renderFrontProgress(x, y, progress, color, sector) {
    const W = 46, H = 6, R = 3;
    const g = arrowLayer.append('g').attr('transform', `translate(${x - W / 2},${y})`);

    // Background
    g.append('rect').attr('width', W).attr('height', H).attr('rx', R)
      .attr('fill', 'rgba(0,0,0,0.65)');

    // Fill — green tint when captured (100%)
    const fillColor = progress >= 1.0 ? '#22c55e' : color;
    g.append('rect').attr('width', Math.min(W, W * progress)).attr('height', H).attr('rx', R)
      .attr('fill', fillColor).attr('opacity', 0.9);

    // Pct + sector label
    const pctLabel = progress >= 1.0 ? '✓' : `${Math.round(progress * 100)}%`;
    const sectorStr = (sector && sector !== 'main') ? ` ${sector.toUpperCase()}` : '';
    g.append('text')
      .attr('x', W / 2).attr('y', H + 10)
      .attr('text-anchor', 'middle')
      .attr('fill', progress >= 1.0 ? '#4ade80' : '#fff')
      .attr('font-size', '8px')
      .attr('font-family', 'Rajdhani, sans-serif')
      .attr('font-weight', '700')
      .text(`${pctLabel}${sectorStr}`);
  }

  // ── Unit counters ─────────────────────────────────────────────────────────

  function _renderCounter(army, gameState) {
    const c = _getCentroid(army.location || gameState.player_nation_id);
    if (!c) return;

    // Get current zoom level so counters maintain fixed screen size regardless of zoom
    const k = (svgEl && svgEl.node) ? (d3.zoomTransform(svgEl.node()).k || 1) : 1;

    const meta    = TEMPLATE_META[army.template_id] || TEMPLATE_META.infantry;
    const isReady = army.is_trained;
    const bgColor = isReady ? meta.color : '#3a4a5a';
    const borderC = army.status === 'attacking' ? '#ef4444' : '#c8d8ea';

    // Offset multiple armies on same territory (in screen pixels, converted to SVG)
    const armiesHere = window._warMapArmyOffsets = window._warMapArmyOffsets || {};
    const key = army.location || 'home';
    armiesHere[key] = (armiesHere[key] || 0);
    const idx = armiesHere[key];
    armiesHere[key]++;

    // Screen-space dimensions (compact HoI4-style counter)
    const SW = 20, SH = 13;
    const screenOffX = (idx % 5) * 23 - 46;
    const screenOffY = Math.floor(idx / 5) * 16;

    // Convert screen offsets to SVG coordinate space (divide by zoom k)
    const svgX = c[0] + screenOffX / k;
    const svgY = c[1] - 6 / k + screenOffY / k;

    const g = counterLayer.append('g')
      .attr('class', 'army-counter')
      // scale(1/k) keeps the counter at fixed screen size despite zoom
      .attr('transform', `translate(${svgX},${svgY}) scale(${1 / k})`)
      .style('cursor', 'pointer')
      .on('click', () => {
        if (typeof window.onArmyCounterClick === 'function') {
          window.onArmyCounterClick(army.id);
        }
      });

    // Outer shadow for depth
    g.append('rect').attr('x', 1).attr('y', 1).attr('width', SW).attr('height', SH).attr('rx', 2)
      .attr('fill', 'rgba(0,0,0,0.5)');

    // Counter body
    g.append('rect').attr('width', SW).attr('height', SH).attr('rx', 2)
      .attr('fill', bgColor).attr('stroke', borderC).attr('stroke-width', 1.2);

    // Template icon text (abbreviated, fits in compact counter)
    g.append('text')
      .attr('x', SW / 2).attr('y', SH / 2 + 3.5)
      .attr('text-anchor', 'middle')
      .attr('fill', '#fff')
      .attr('font-size', '6.5px')
      .attr('font-family', 'Rajdhani, sans-serif')
      .attr('font-weight', '700')
      .text(meta.icon);

    // Division count badge (top-right corner)
    g.append('rect')
      .attr('x', SW - 7).attr('y', -1).attr('width', 8).attr('height', 8).attr('rx', 1.5)
      .attr('fill', '#0d1b2a').attr('stroke', borderC).attr('stroke-width', 0.8);
    g.append('text')
      .attr('x', SW - 3).attr('y', 6)
      .attr('text-anchor', 'middle').attr('fill', '#ffd700')
      .attr('font-size', '5.5px').attr('font-weight', '700')
      .text(army.num_divisions);

    // Training progress bar (below counter)
    if (!isReady) {
      const prog = army.training_progress / Math.max(1, army.training_turns_required);
      g.append('rect').attr('y', SH).attr('width', SW).attr('height', 2)
        .attr('fill', '#0f1e30');
      g.append('rect').attr('y', SH).attr('width', SW * prog).attr('height', 2)
        .attr('fill', '#f59e0b');
    }

    // Attacking pulse dot
    if (army.status === 'attacking' && army.assigned_target) {
      g.append('circle')
        .attr('cx', SW / 2).attr('cy', SH + 5).attr('r', 2.5)
        .attr('fill', '#ef4444').attr('class', 'attack-pulse');
    }

    // Tooltip on hover
    g.on('mouseover', function(event) {
      _showCounterTooltip(event, army, meta, gameState);
    }).on('mouseout', _hideCounterTooltip);
  }

  // ── Front line visualization ───────────────────────────────────────────────

  function _renderFrontLines(gameState) {
    if (!warLayer) return;
    for (const war of (gameState.active_wars || [])) {
      if (war.status !== 'ongoing') continue;

      const attacker = gameState.nations[war.attacker];
      const defender = gameState.nations[war.defender];
      if (!attacker || !defender) continue;

      const attColor = '#ef4444';  // red for attacker
      const defColor = '#3b82f6';  // blue for defender

      // Highlight the defender's territory with an animated pulse border
      const defIso = (COUNTRY_DATA.nameToISO || {})[defender.name.toLowerCase()];
      if (defIso) {
        const defPath = d3.select(`#country-${defIso}`);
        if (!defPath.empty()) {
          const d = defPath.datum();
          if (d) {
            // Pulsing attacker-colored border
            warLayer.append('path')
              .attr('d', pathFn(d))
              .attr('fill', 'none')
              .attr('stroke', attColor)
              .attr('stroke-width', 2.5)
              .attr('stroke-opacity', 0.7)
              .attr('stroke-dasharray', '6 3')
              .attr('class', 'front-line front-line-active')
              .style('animation', 'front-pulse 1.5s ease-in-out infinite');

            // Interior progress gradient overlay
            const progressVal = war.fronts && war.fronts.length > 0
              ? war.fronts.reduce((s, f) => s + f.progress, 0) / war.fronts.length
              : (war.attacker_warscore + 100) / 200;
            if (progressVal > 0.1) {
              warLayer.append('path')
                .attr('d', pathFn(d))
                .attr('fill', attColor)
                .attr('fill-opacity', Math.min(0.35, progressVal * 0.4))
                .attr('class', 'front-progress-overlay');
            }
          }
        }
      }

      // Also highlight attacker territory for context
      const attIso = (COUNTRY_DATA.nameToISO || {})[attacker.name.toLowerCase()];
      if (attIso) {
        const attPath = d3.select(`#country-${attIso}`);
        if (!attPath.empty()) {
          const d = attPath.datum();
          if (d) {
            warLayer.append('path')
              .attr('d', pathFn(d))
              .attr('fill', 'none')
              .attr('stroke', attColor)
              .attr('stroke-width', 1.5)
              .attr('stroke-opacity', 0.5)
              .attr('class', 'front-line front-line-attacker');
          }
        }
      }
    }
  }

  function _showCounterTooltip(event, army, meta, gameState) {
    let tip = document.getElementById('war-counter-tip');
    if (!tip) {
      tip = document.createElement('div');
      tip.id = 'war-counter-tip';
      tip.style.cssText = [
        'position:fixed', 'background:rgba(10,18,30,0.97)',
        'border:1px solid #3b5c8c', 'color:#c9d8ea', 'padding:8px 12px',
        'border-radius:6px', 'font-size:12px', 'font-family:Rajdhani,sans-serif',
        'pointer-events:none', 'z-index:9000', 'min-width:140px',
        'box-shadow:0 4px 16px rgba(0,0,0,0.5)'
      ].join(';');
      document.body.appendChild(tip);
    }
    const statusLabel = {
      training: `🔧 Training (${army.training_progress}/${army.training_turns_required})`,
      ready: '✓ Ready',
      attacking: `⚔ Attacking ${gameState.nations[army.assigned_target]?.name || '?'}`,
      defending: '🛡 Defending',
    }[army.status] || army.status;

    tip.innerHTML = `
      <div style="font-weight:700;color:#e8c97a;margin-bottom:4px">${army.name}</div>
      <div style="color:#8cb4e0;margin-bottom:2px">${meta.label} · ${army.num_divisions} div.</div>
      <div>${statusLabel}</div>
      <div style="margin-top:4px;color:#aaa">
        Strength ${Math.round(army.strength * 100)}% · Org ${Math.round(army.organization * 100)}%
      </div>
    `;
    tip.style.left = (event.clientX + 14) + 'px';
    tip.style.top  = (event.clientY - 10) + 'px';
    tip.style.display = 'block';
  }

  function _hideCounterTooltip() {
    const tip = document.getElementById('war-counter-tip');
    if (tip) tip.style.display = 'none';
  }

  // ── Clear helpers ─────────────────────────────────────────────────────────

  function _clearLayers() {
    if (warLayer)     warLayer.selectAll('*').remove();
    if (arrowLayer)   arrowLayer.selectAll('*').remove();
    if (counterLayer) counterLayer.selectAll('*').remove();
    window._warMapArmyOffsets = {};
  }

  function clear() { _clearLayers(); }

  /**
   * Call when the map projection/path changes (e.g. on resize).
   * Invalidates cached centroids so they are recomputed on next update.
   */
  function onResize(newPathFn, newProjFn) {
    pathFn = newPathFn;
    projFn = newProjFn;
    // Invalidate all centroid caches
    Object.keys(_centroids).forEach(k => delete _centroids[k]);
    Object.keys(_nationCentroids).forEach(k => delete _nationCentroids[k]);
  }

  return { init, update, clear, onResize };
})();

window.WarMapModule = WarMapModule;
