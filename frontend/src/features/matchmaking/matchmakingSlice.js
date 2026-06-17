import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import {
  joinQueue,
  leaveQueue,
  getQueueStatus,
} from '../../services/matchmakingApi';

export const submitJoinQueue = createAsyncThunk(
  'matchmaking/join',
  async (payload, { rejectWithValue }) => {
    try {
      return await joinQueue(payload);
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

export const submitLeaveQueue = createAsyncThunk(
  'matchmaking/leave',
  async (playerId, { rejectWithValue }) => {
    try {
      return await leaveQueue(playerId);
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

export const fetchQueueStatus = createAsyncThunk(
  'matchmaking/status',
  async (playerId, { rejectWithValue }) => {
    try {
      return await getQueueStatus(playerId);
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

const matchmakingSlice = createSlice({
  name: 'matchmaking',
  initialState: {
    // null | QueueStatusResponse | LobbyFormedResponse
    result: null,
    // 'idle' | 'queue' | 'lobby'
    resultType: 'idle',
    loading: false,
    error: null,
  },
  reducers: {
    clearMatchmaking(state) {
      state.result = null;
      state.resultType = 'idle';
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Join
      .addCase(submitJoinQueue.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(submitJoinQueue.fulfilled, (state, action) => {
        state.loading = false;
        state.result = action.payload;
        // Discriminate response type by presence of 'players' array
        state.resultType = Array.isArray(action.payload.players) ? 'lobby' : 'queue';
      })
      .addCase(submitJoinQueue.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Leave
      .addCase(submitLeaveQueue.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(submitLeaveQueue.fulfilled, (state) => {
        state.loading = false;
        state.result = null;
        state.resultType = 'idle';
      })
      .addCase(submitLeaveQueue.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Status poll
      .addCase(fetchQueueStatus.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchQueueStatus.fulfilled, (state, action) => {
        state.loading = false;
        state.result = action.payload;
        state.resultType = 'queue';
      })
      .addCase(fetchQueueStatus.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export const { clearMatchmaking } = matchmakingSlice.actions;
export default matchmakingSlice.reducer;
