import api from './api';

// GET /leaderboard/global?page=&page_size=
// Returns: LeaderboardResponse { total, page, page_size, entries[] }
export const getGlobalLeaderboard = ({ page = 1, pageSize = 20 } = {}) =>
  api
    .get('/leaderboard/global', { params: { page, page_size: pageSize } })
    .then((r) => r.data);

// GET /leaderboard/region/{region}?page=&page_size=
// region values: 'India' | 'SEA' | 'Europe'
export const getRegionLeaderboard = (region, { page = 1, pageSize = 20 } = {}) =>
  api
    .get(`/leaderboard/region/${encodeURIComponent(region)}`, {
      params: { page, page_size: pageSize },
    })
    .then((r) => r.data);

// GET /leaderboard/mode/{game_mode}?page=&page_size=
// game_mode values: 'SOLO' | 'DUO' | 'SQUAD'
export const getModeLeaderboard = (gameMode, { page = 1, pageSize = 20 } = {}) =>
  api
    .get(`/leaderboard/mode/${gameMode}`, { params: { page, page_size: pageSize } })
    .then((r) => r.data);

// GET /leaderboard/region/{region}/mode/{game_mode}?page=&page_size=
export const getRegionModeLeaderboard = (
  region,
  gameMode,
  { page = 1, pageSize = 20 } = {}
) =>
  api
    .get(
      `/leaderboard/region/${encodeURIComponent(region)}/mode/${gameMode}`,
      { params: { page, page_size: pageSize } }
    )
    .then((r) => r.data);
