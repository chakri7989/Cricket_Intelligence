const API_BASE = '/api';

export const api = {
  // Query AI Intelligence
  async askQuery(query) {
    const res = await fetch(`${API_BASE}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to process intelligence query');
    }
    return res.json();
  },

  // Get Live Matches
  async getLiveMatches() {
    const res = await fetch(`${API_BASE}/matches/live`);
    if (!res.ok) throw new Error('Failed to fetch live matches');
    return res.json();
  },

  // Get Scorecard for match
  async getMatchScorecard(matchId) {
    const res = await fetch(`${API_BASE}/matches/${matchId}`);
    if (!res.ok) throw new Error('Failed to fetch scorecard');
    return res.json();
  },

  // Compare two players
  async comparePlayers(p1, p2) {
    const params = new URLSearchParams({ p1, p2 });
    const res = await fetch(`${API_BASE}/players/compare?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to compare players');
    return res.json();
  },

  // List players
  async getPlayers() {
    const res = await fetch(`${API_BASE}/players/list`);
    if (!res.ok) throw new Error('Failed to fetch players');
    return res.json();
  },

  // Historical Vault Matches
  async getVaultMatches() {
    const res = await fetch(`${API_BASE}/vault/matches`);
    if (!res.ok) throw new Error('Failed to fetch historical matches');
    return res.json();
  },

  // System Status
  async getSystemStatus() {
    const res = await fetch(`${API_BASE}/system/status`);
    if (!res.ok) throw new Error('Failed to fetch system status');
    return res.json();
  }
};

