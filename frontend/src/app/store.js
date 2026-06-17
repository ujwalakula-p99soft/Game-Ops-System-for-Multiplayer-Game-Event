import { configureStore } from '@reduxjs/toolkit';
import leaderboardReducer from '../features/leaderboard/leaderboardSlice';
import matchmakingReducer from '../features/matchmaking/matchmakingSlice';
import suspiciousReducer from '../features/suspicious/suspiciousSlice';

const store = configureStore({
  reducer: {
    leaderboard: leaderboardReducer,
    matchmaking: matchmakingReducer,
    suspicious: suspiciousReducer,
  },
});

export default store;
