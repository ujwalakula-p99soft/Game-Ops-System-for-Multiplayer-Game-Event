import api from './api';

// POST /matchmaking/join
// Body: { player_id: str, game_mode: str, ping: int (>=0) }
// Returns: QueueStatusResponse | LobbyFormedResponse
// Discriminate by presence of `players` array in response
export const joinQueue = (payload) =>
  api.post('/matchmaking/join', payload).then((r) => r.data);

// POST /matchmaking/leave?player_id=xxx
// player_id is a QUERY PARAM — not a body field
// Returns: LeaveQueueResponse { player_id, message }
export const leaveQueue = (playerId) =>
  api
    .post('/matchmaking/leave', null, { params: { player_id: playerId } })
    .then((r) => r.data);

// GET /matchmaking/{player_id}
// Returns: QueueStatusResponse
export const getQueueStatus = (playerId) =>
  api.get(`/matchmaking/${playerId}`).then((r) => r.data);
