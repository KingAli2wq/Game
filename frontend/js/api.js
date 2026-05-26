// API client for the backend

const API = {
  async request(method, path, body = null, signal = null) {
    const opts = {
      method,
      headers: { 'Content-Type': 'application/json' },
    };
    if (body !== null) opts.body = JSON.stringify(body);
    if (signal) opts.signal = signal;
    const res = await fetch(path, opts);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },

  get: (path) => API.request('GET', path),
  post: (path, body) => API.request('POST', path, body),
  del: (path) => API.request('DELETE', path),

  status: () => API.get('/api/status'),
  getEras: () => API.get('/api/eras'),
  getSaves: () => API.get('/api/saves'),

  newGame: (era_id, player_nation_name, ideology, signal) =>
    API.request('POST', '/api/game/new', { era_id, player_nation_name, ideology }, signal),

  getState: (gameId) => API.get(`/api/game/${gameId}`),
  deleteGame: (gameId) => API.del(`/api/game/${gameId}`),

  advanceTurn: (gameId) => API.post(`/api/game/${gameId}/turn`),

  getIssues: (gameId) => API.get(`/api/game/${gameId}/issues`),
  respondToIssue: (gameId, issueId, optionId) =>
    API.post(`/api/game/${gameId}/issue/${issueId}/respond`, { option_id: optionId }),

  sendDiplomacy: (gameId, action_type, target_nation, details = {}) =>
    API.post(`/api/game/${gameId}/diplomacy`, { action_type, target_nation, details }),

  declareWar: (gameId, target_nation, casus_belli = 'territorial_dispute') =>
    API.post(`/api/game/${gameId}/war/declare`, { target_nation, casus_belli }),

  getPeaceTerms: (gameId, warId) => API.get(`/api/game/${gameId}/peace_terms/${warId}`),

  makePeace: (gameId, warId, term_id) =>
    API.post(`/api/game/${gameId}/war/${warId}/peace`, { term_id }),

  getEconomyPolicy: (gameId) => API.get(`/api/game/${gameId}/economy/policy`),
  setEconomyPolicy: (gameId, policy) =>
    API.post(`/api/game/${gameId}/economy/policy`, policy),

  getNation: (gameId, nationId) => API.get(`/api/game/${gameId}/nation/${nationId}`),

  // Resource trades
  proposeResourceTrade: (gameId, body) =>
    API.post(`/api/game/${gameId}/diplomacy/resource-trade`, body),
  getResourceTrades: (gameId) => API.get(`/api/game/${gameId}/resource-trades`),
  cancelResourceTrade: (gameId, tradeId) => API.del(`/api/game/${gameId}/resource-trades/${tradeId}`),

  // Advanced diplomacy
  requestTroops: (gameId, body) =>
    API.post(`/api/game/${gameId}/diplomacy/request-troops`, body),
  buyTechnology: (gameId, body) =>
    API.post(`/api/game/${gameId}/diplomacy/buy-technology`, body),
  jointResearch: (gameId, body) =>
    API.post(`/api/game/${gameId}/diplomacy/joint-research`, body),
  upgradeAlliance: (gameId, body) =>
    API.post(`/api/game/${gameId}/diplomacy/upgrade-alliance`, body),

  // Policies
  getPolicies: (gameId) => API.get(`/api/game/${gameId}/policies`),
  togglePolicy: (gameId, body) => API.post(`/api/game/${gameId}/toggle-policy`, body),

  // Research
  startResearch: (gameId, body) => API.post(`/api/game/${gameId}/research/start`, body),
  cancelResearch: (gameId, body) => API.post(`/api/game/${gameId}/research/cancel`, body),
};

window.API = API;
