import api from './api';

// POST /players
// Body: { player_id: str, region: str, device: str }
// Returns: PlayerResponse
export const createPlayer = (payload) =>
  api.post('/players', payload).then((r) => r.data);

// GET /players/{player_id}
// Returns: PlayerResponse
export const getPlayer = (playerId) =>
  api.get(`/players/${playerId}`).then((r) => r.data);
