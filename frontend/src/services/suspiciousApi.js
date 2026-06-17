import api from './api';

// GET /suspicious-players
// Returns: SuspiciousPlayersResponse { total, entries[] }
export const getSuspiciousPlayers = () =>
  api.get('/suspicious-players').then((r) => r.data);
