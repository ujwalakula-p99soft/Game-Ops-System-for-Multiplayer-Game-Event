// Exact enum values from backend app/utils/enums.py
export const REGIONS = ['India', 'SEA', 'Europe'];

export const DEVICE_TYPES = ['Android', 'iOS', 'PC', 'Console'];

export const GAME_MODES = ['SOLO', 'DUO', 'SQUAD'];

export const RANK_TIERS = ['Bronze', 'Silver', 'Gold', 'Platinum'];

// Leaderboard filter options — each maps to a backend endpoint
export const LEADERBOARD_REGION_FILTERS = [
  { key: 'global', label: 'Global' },
  { key: 'India',  label: 'India' },
  { key: 'SEA',    label: 'SEA' },
  { key: 'Europe', label: 'Europe' },
];

export const LEADERBOARD_MODE_FILTERS = [
  { key: 'all',   label: 'All Modes' },
  { key: 'SOLO',  label: 'SOLO' },
  { key: 'DUO',   label: 'DUO' },
  { key: 'SQUAD', label: 'SQUAD' },
];

// Rank tier display config
export const RANK_CONFIG = {
  Bronze:   { color: 'text-amber-600',  bg: 'bg-amber-600/10',  border: 'border-amber-600/30' },
  Silver:   { color: 'text-slate-300',  bg: 'bg-slate-300/10',  border: 'border-slate-300/30' },
  Gold:     { color: 'text-yellow-400', bg: 'bg-yellow-400/10', border: 'border-yellow-400/30' },
  Platinum: { color: 'text-cyan-400',   bg: 'bg-cyan-400/10',   border: 'border-cyan-400/30' },
};

// Lobby size per mode — mirrors backend LOBBY_SIZE
export const LOBBY_SIZE = {
  SOLO:  1,
  DUO:   2,
  SQUAD: 4,
};
