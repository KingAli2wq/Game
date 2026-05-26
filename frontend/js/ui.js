// UI helpers and notification system

const UI = (() => {
  const notifications = [];

  function notify(message, type = 'info', duration = 4000) {
    const container = document.getElementById('notifications');
    if (!container) return;

    const el = document.createElement('div');
    el.className = `notification ${type}`;
    el.textContent = message;
    container.appendChild(el);
    notifications.push(el);

    setTimeout(() => {
      el.style.opacity = '0';
      el.style.transform = 'translateX(100%)';
      el.style.transition = 'all 0.3s';
      setTimeout(() => {
        el.remove();
        const i = notifications.indexOf(el);
        if (i > -1) notifications.splice(i, 1);
      }, 300);
    }, duration);
  }

  function showLoading(message = 'Processing...', showCancel = false) {
    const overlay = document.getElementById('loading-overlay');
    if (!overlay) return;
    overlay.classList.remove('hidden');
    const text = overlay.querySelector('.loading-text');
    if (text) text.textContent = message;
    const cancelBtn = overlay.querySelector('#loading-cancel-btn');
    if (cancelBtn) cancelBtn.classList.toggle('hidden', !showCancel);
  }

  function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.classList.add('hidden');
  }

  function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    const screen = document.getElementById(screenId);
    if (screen) screen.classList.add('active');
  }

  function showModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.remove('hidden');
  }

  function hideModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.add('hidden');
  }

  function setTab(tabGroupId, tabId) {
    const group = document.getElementById(tabGroupId);
    if (!group) return;
    group.querySelectorAll('.tab-btn').forEach(b => {
      b.classList.toggle('active', b.dataset.tab === tabId);
    });
    // Tab content is a sibling of the tab bar, not a child — search the parent
    const panel = group.parentElement;
    if (panel) panel.querySelectorAll('.tab-content').forEach(c => {
      c.classList.toggle('active', c.id === tabId);
    });
  }

  function pct(value, total) {
    return Math.min(100, Math.max(0, (value / total) * 100)).toFixed(1) + '%';
  }

  function fmt(num, decimals = 1) {
    if (typeof num !== 'number') return '—';
    if (Math.abs(num) >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toFixed(decimals);
  }

  function fmtGDP(gdp) {
    if (gdp >= 1000) return '$' + (gdp / 1000).toFixed(2) + 'T';
    return '$' + gdp.toFixed(0) + 'B';
  }

  function fmtPct(val) {
    return (val * 100).toFixed(1) + '%';
  }

  function fmtArmy(n) {
    if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
    if (n >= 1_000) return (n / 1_000).toFixed(0) + 'K';
    return n.toString();
  }

  function statBar(label, value, max, colorClass = 'fill-blue', subtitle = '') {
    const pctVal = Math.min(100, Math.max(0, (value / max) * 100));
    return `
      <div class="stat-row">
        <div class="stat-header">
          <span class="stat-name">${label}</span>
          <span class="stat-value">${subtitle || value}</span>
        </div>
        <div class="stat-bar">
          <div class="stat-fill ${colorClass}" style="width:${pctVal}%"></div>
        </div>
      </div>`;
  }

  function relationBadge(rel) {
    if (rel > 30) return `<span class="relation-badge rel-positive">+${rel}</span>`;
    if (rel < -30) return `<span class="relation-badge rel-negative">${rel}</span>`;
    return `<span class="relation-badge rel-neutral">${rel}</span>`;
  }

  function ideologyColor(ideology) {
    const colors = {
      'Liberal Democracy': '#3b82f6', 'Social Democracy': '#22c55e',
      'Conservative Democracy': '#f59e0b', 'Socialism': '#ef4444',
      'Communism': '#dc2626', 'Fascism': '#78716c', 'Monarchy': '#7c3aed',
      'Theocracy': '#059669', 'Technocracy': '#0ea5e9', 'Oligarchy': '#a8a29e',
    };
    return colors[ideology] || '#888888';
  }

  function monthName(month) {
    const names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    return names[(month - 1) % 12] || '?';
  }

  return {
    notify, showLoading, hideLoading, showScreen, showModal, hideModal,
    setTab, pct, fmt, fmtGDP, fmtPct, fmtArmy, statBar, relationBadge,
    ideologyColor, monthName
  };
})();

window.UI = UI;
