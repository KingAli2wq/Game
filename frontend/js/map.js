// D3.js World Map Module — 50m resolution, local data, comprehensive ISO lookup

const MapModule = (() => {
  let svg, g, projection, path, zoom;
  let currentGameState = null;
  let onCountryClick = null;
  let countryNameMap = {};  // ISO numeric -> display name
  let _tooltipRafId = null;  // requestAnimationFrame handle for throttled tooltip

  // Use COUNTRY_DATA from country-data.js (loaded before this file)
  // COUNTRY_DATA.nameToISO  : lowercase name -> ISO numeric
  // COUNTRY_DATA.nameToAlpha2: lowercase name -> alpha-2

  function getAlpha2(nationName) {
    if (!nationName) return null;
    return (COUNTRY_DATA.nameToAlpha2 || {})[nationName.toLowerCase()] || null;
  }

  function flagUrl(nationName) {
    const a2 = getAlpha2(nationName);
    return a2 ? `https://flagcdn.com/w40/${a2}.png` : null;
  }

  function init(containerId, clickCallback) {
    onCountryClick = clickCallback;
    const container = document.getElementById(containerId);
    if (!container) return;

    const W = container.clientWidth;
    const H = container.clientHeight;

    svg = d3.select(`#${containerId}`)
      .append('svg')
      .attr('id', 'world-map')
      .attr('width', W)
      .attr('height', H);

    // Ocean background
    svg.append('rect')
      .attr('width', W)
      .attr('height', H)
      .attr('fill', '#070c18');

    g = svg.append('g');

    projection = d3.geoNaturalEarth1()
      .scale(W / 6.3)
      .translate([W / 2, H / 2]);

    path = d3.geoPath().projection(projection);

    zoom = d3.zoom()
      .scaleExtent([0.7, 10])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      })
      .on('start', () => {
        // Disable pointer-events on paths during drag/zoom for smoother panning
        g.selectAll('.country-path').style('pointer-events', 'none');
        hideTooltip();
      })
      .on('end', () => {
        g.selectAll('.country-path').style('pointer-events', null);
      });

    svg.call(zoom);

    // Load local 50m world data (downloaded from world-atlas)
    fetch('/static/data/countries-50m.json')
      .then(r => r.json())
      .then(world => {
        const countries = topojson.feature(world, world.objects.countries);
        const borders   = topojson.mesh(world, world.objects.countries, (a, b) => a !== b);
        const land      = topojson.merge(world, world.objects.countries.geometries);

        // Subtle coastline shadow — NO filter (SVG filters kill GPU compositing)
        g.append('path')
          .datum(land)
          .attr('class', 'land-shadow')
          .attr('d', path)
          .attr('fill', 'none')
          .attr('stroke', '#0a0f20')
          .attr('stroke-width', 2.5)
          .attr('opacity', 0.4)
          .style('pointer-events', 'none');

        // Graticule — non-interactive, rendered below countries
        const graticule = d3.geoGraticule()();
        g.append('path')
          .datum(graticule)
          .attr('d', path)
          .attr('fill', 'none')
          .attr('stroke', '#141e30')
          .attr('stroke-width', 0.3)
          .style('pointer-events', 'none');

        // Countries
        g.selectAll('.country-path')
          .data(countries.features)
          .enter()
          .append('path')
          .attr('class', 'country-path')
          .attr('d', path)
          .attr('id', d => `country-${d.id}`)
          .attr('fill', '#1e2d45')
          .on('click', (event, d) => handleCountryClick(event, d))
          .on('mouseover', (event, d) => showTooltip(event, d))
          .on('mousemove', (event) => moveTooltip(event))
          .on('mouseout', hideTooltip);

        // Borders — non-interactive decorative layer
        g.append('path')
          .datum(borders)
          .attr('d', path)
          .attr('fill', 'none')
          .attr('stroke', '#111825')
          .attr('stroke-width', 0.4)
          .style('pointer-events', 'none');

        buildCountryNameMap(countries.features);
        // Container may have been hidden (0×0) at init time — resize now that data is ready
        resize();
        if (currentGameState) updateColors(currentGameState);
        _fireReady();
      })
      .catch(err => {
        console.error('Local map failed, falling back to CDN:', err);
        fetch('https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json')
          .then(r => r.json())
          .then(world => {
            const countries = topojson.feature(world, world.objects.countries);
            const borders   = topojson.mesh(world, world.objects.countries, (a, b) => a !== b);
            g.selectAll('.country-path')
              .data(countries.features)
              .enter().append('path')
              .attr('class', 'country-path').attr('d', path)
              .attr('id', d => `country-${d.id}`).attr('fill', '#1e2d45')
              .on('click', (event, d) => handleCountryClick(event, d))
              .on('mouseover', (event, d) => showTooltip(event, d))
              .on('mousemove', (event) => moveTooltip(event))
              .on('mouseout', hideTooltip);
            g.append('path').datum(borders).attr('d', path)
              .attr('fill', 'none').attr('stroke', '#111825').attr('stroke-width', 0.4);
            buildCountryNameMap(countries.features);
            resize();
            if (currentGameState) updateColors(currentGameState);
            _fireReady();
          });
      });
  }

  function buildCountryNameMap(features) {
    // Build numeric-id -> display name using the comprehensive COUNTRY_DATA
    // COUNTRY_DATA.nameToISO maps name->numeric; invert it
    const numToName = {};
    for (const [name, num] of Object.entries(COUNTRY_DATA.nameToISO || {})) {
      // Prefer proper-cased names (first char uppercase)
      if (!numToName[num] || name[0] === name[0].toUpperCase()) {
        numToName[num] = name.charAt(0).toUpperCase() + name.slice(1);
      }
    }
    features.forEach(f => {
      if (numToName[f.id]) countryNameMap[f.id] = numToName[f.id];
    });
  }

  function getNationForCountry(countryId) {
    const name = countryNameMap[countryId];
    if (!name || !currentGameState) return null;
    const nameLower = name.toLowerCase();
    for (const [nid, nation] of Object.entries(currentGameState.nations)) {
      const nl = nation.name.toLowerCase();
      if (nl === nameLower) return { nid, nation };
    }
    // Partial match: first word
    for (const [nid, nation] of Object.entries(currentGameState.nations)) {
      const nl = nation.name.toLowerCase();
      if (nl.includes(nameLower.split(' ')[0]) || nameLower.includes(nl.split(' ')[0])) {
        return { nid, nation };
      }
    }
    return null;
  }

  function handleCountryClick(event, d) {
    event.stopPropagation();
    const match = getNationForCountry(d.id);
    if (match && onCountryClick) onCountryClick(match.nid, match.nation);
  }

  function showTooltip(event, d) {
    const tooltip = document.getElementById('map-tooltip');
    if (!tooltip) return;
    const name = countryNameMap[d.id] || `Country ${d.id}`;
    const match = getNationForCountry(d.id);
    const nation = match?.nation;

    if (nation) {
      const a2 = getAlpha2(nation.name);
      const flagHtml = a2
        ? `<img class="tooltip-flag-img" src="https://flagcdn.com/w40/${a2}.png" alt="" onerror="this.style.display='none'">`
        : '';
      const stability = Math.round((nation.stability || 0) * 100);
      const army = nation.military?.total_divisions ?? nation.military?.army_size ?? '?';
      const gdp = nation.economy?.gdp?.toFixed(0) ?? '?';
      const warTag = nation.is_at_war
        ? `<div class="tooltip-war-tag"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m14.5 17.5-5-5 5-5m-9 5h14"/></svg>AT WAR</div>`
        : '';

      tooltip.innerHTML = `
        <div class="tooltip-header">
          ${flagHtml}
          <div class="tooltip-name">${nation.name}</div>
        </div>
        <div class="tooltip-ideology">${nation.ideology}</div>
        <div class="tooltip-stats">
          <div class="tooltip-stat-row">
            <span>GDP</span><span class="tooltip-stat-val" style="color:var(--gold)">$${gdp}B</span>
          </div>
          <div class="tooltip-stat-row">
            <span>Army</span><span class="tooltip-stat-val">${army} div.</span>
          </div>
          <div class="tooltip-stat-row">
            <span>Stability</span><span class="tooltip-stat-val">${stability}%</span>
          </div>
          <div class="tooltip-mini-bar"><div class="tooltip-mini-fill" style="width:${stability}%"></div></div>
          ${warTag}
        </div>`;
    } else {
      tooltip.innerHTML = `<div class="tooltip-name">${name}</div><div class="tooltip-ideology" style="color:var(--text-dim)">No active nation</div>`;
    }

    tooltip.style.display = 'block';
    moveTooltip(event);
  }

  function moveTooltip(event) {
    // Throttle via rAF so we don't force a layout recalc on every mousemove pixel
    if (_tooltipRafId) return;
    const cx = event.clientX, cy = event.clientY;
    _tooltipRafId = requestAnimationFrame(() => {
      _tooltipRafId = null;
      const tooltip = document.getElementById('map-tooltip');
      if (!tooltip || tooltip.style.display === 'none') return;
      let x = cx + 16;
      let y = cy - 14;
      const w = tooltip.offsetWidth || 180;
      if (x + w > window.innerWidth - 8) x = cx - w - 8;
      if (y < 4) y = 4;
      tooltip.style.left = x + 'px';
      tooltip.style.top  = y + 'px';
    });
  }

  function hideTooltip() {
    const el = document.getElementById('map-tooltip');
    if (el) el.style.display = 'none';
  }

  const IDEOLOGY_MAP_COLORS = {
    'Liberal Democracy':      '#1d4ed8',
    'Social Democracy':       '#15803d',
    'Conservative Democracy': '#b45309',
    'Socialism':              '#b91c1c',
    'Communism':              '#7f1d1d',
    'Fascism':                '#292524',
    'Monarchy':               '#6d28d9',
    'Theocracy':              '#065f46',
    'Technocracy':            '#0369a1',
    'Oligarchy':              '#44403c',
  };

  function updateColors(gameState) {
    currentGameState = gameState;
    if (!gameState) return;

    const isoToNation = {};
    for (const [nid, nation] of Object.entries(gameState.nations)) {
      const num = (COUNTRY_DATA.nameToISO || {})[nation.name.toLowerCase()];
      if (num) isoToNation[num] = { id: nid, nation };
    }

    // Build reverse map: territory_id -> controlling nation
    const territoryController = {};
    for (const [nid, nation] of Object.entries(gameState.nations)) {
      if (nation.is_alive) {
        for (const tid of (nation.controlled_territories || [])) {
          territoryController[tid] = { id: nid, nation };
        }
      }
    }

    d3.selectAll('.country-path').each(function(d) {
      const el    = d3.select(this);
      const match = isoToNation[d.id];
      if (match) {
        const nation = match.nation;
        if (!nation.is_alive) {
          // Check if this territory is controlled by another nation
          const controller = territoryController[match.id];
          if (controller) {
            const ctrlColor = IDEOLOGY_MAP_COLORS[controller.nation.ideology] || '#1e2d45';
            // Darken the color slightly to distinguish from sovereign territory
            el.attr('fill', ctrlColor)
              .attr('opacity', 0.65)
              .classed('player', false)
              .classed('at-war', false);
          } else {
            el.attr('fill', '#0c0c18').attr('opacity', 1)
              .classed('player', false).classed('at-war', false);
          }
        } else {
          const color = IDEOLOGY_MAP_COLORS[nation.ideology] || '#1e2d45';
          el.attr('fill', color).attr('opacity', 1)
            .classed('player',  nation.is_player)
            .classed('at-war',  nation.is_at_war);
        }
      } else {
        el.attr('fill', '#1c2a40').attr('opacity', 1);
      }
    });

    renderLegend(gameState);
  }

  function renderLegend(gameState) {
    const el = document.getElementById('ideology-legend');
    if (!el) return;
    const present = new Set();
    for (const nation of Object.values(gameState.nations)) {
      if (nation.is_alive) present.add(nation.ideology);
    }
    el.innerHTML = Array.from(present).sort().map(ideo => `
      <div class="legend-item">
        <div class="legend-dot" style="background:${IDEOLOGY_MAP_COLORS[ideo] || '#888'}"></div>
        <span>${ideo}</span>
      </div>`).join('');
  }

  function highlightNation(nationId) {
    if (!currentGameState) return;
    const nation = currentGameState.nations[nationId];
    if (!nation) return;
    const num = (COUNTRY_DATA.nameToISO || {})[nation.name.toLowerCase()];
    if (num) {
      d3.selectAll('.country-path').classed('selected', false);
      d3.select(`#country-${num}`).classed('selected', true);
    }
  }

  function resize() {
    if (!svg) return;
    const container = document.getElementById('map-container');
    if (!container) return;
    const W = container.clientWidth;
    const H = container.clientHeight;
    svg.attr('width', W).attr('height', H);
    projection.translate([W / 2, H / 2]).scale(W / 6.3);
    path = d3.geoPath().projection(projection);
    g.selectAll('path').attr('d', path);
    // Notify WarMapModule that projection changed
    if (window.WarMapModule) window.WarMapModule.onResize(path, projection);
  }

  // Expose internals for WarMapModule overlay integration
  function getInternals() {
    return { svg, g, projection, path };
  }

  // Hooks to call after map data is fully loaded
  const _readyCallbacks = [];
  let _dataReady = false;
  function onReady(cb) {
    if (_dataReady) { cb(); return; }
    _readyCallbacks.push(cb);
  }
  function _fireReady() {
    _dataReady = true;
    _readyCallbacks.forEach(cb => { try { cb(); } catch(e) {} });
    _readyCallbacks.length = 0;
  }

  return { init, updateColors, highlightNation, resize, flagUrl, getAlpha2, getInternals, onReady };
})();

window.MapModule = MapModule;
