import api from './api';

// POST /matches
// Body: {
//   match_id: str,
//   game_mode: 'SOLO'|'DUO'|'SQUAD',
//   match_duration_seconds: int (>0),
//   results: [{ player_id, ping, score, kills, deaths }]  (1–100 items)
// }
// Returns: MatchResponse
export const createMatch = (payload) =>
  api.post('/matches', payload).then((r) => r.data);
