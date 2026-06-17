import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import {
  getGlobalLeaderboard,
  getRegionLeaderboard,
  getModeLeaderboard,
  getRegionModeLeaderboard,
} from '../../services/leaderboardApi';

// Async thunks — one per endpoint
export const fetchGlobalLeaderboard = createAsyncThunk(
  'leaderboard/fetchGlobal',
  async ({ page, pageSize }, { rejectWithValue }) => {
    try {
      return await getGlobalLeaderboard({ page, pageSize });
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

export const fetchRegionLeaderboard = createAsyncThunk(
  'leaderboard/fetchRegion',
  async ({ region, page, pageSize }, { rejectWithValue }) => {
    try {
      return await getRegionLeaderboard(region, { page, pageSize });
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

export const fetchModeLeaderboard = createAsyncThunk(
  'leaderboard/fetchMode',
  async ({ gameMode, page, pageSize }, { rejectWithValue }) => {
    try {
      return await getModeLeaderboard(gameMode, { page, pageSize });
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

export const fetchRegionModeLeaderboard = createAsyncThunk(
  'leaderboard/fetchRegionMode',
  async ({ region, gameMode, page, pageSize }, { rejectWithValue }) => {
    try {
      return await getRegionModeLeaderboard(region, gameMode, { page, pageSize });
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

const leaderboardSlice = createSlice({
  name: 'leaderboard',
  initialState: {
    regionFilter: 'global',
    modeFilter: 'all',
    // Pagination
    page: 1,
    pageSize: 20,
    // Data
    entries: [],
    total: 0,
    // Async state
    loading: false,
    error: null,
  },
  reducers: {
    setRegionFilter(state, action) {
      state.regionFilter = action.payload;
      state.page = 1;
      state.entries = [];
      state.error = null;
    },
    setModeFilter(state, action) {
      state.modeFilter = action.payload;
      state.page = 1;
      state.entries = [];
      state.error = null;
    },
    setPage(state, action) {
      state.page = action.payload;
    },
    setPageSize(state, action) {
      state.pageSize = action.payload;
      state.page = 1;
    },
  },
  extraReducers: (builder) => {
    const handlePending = (state) => {
      state.loading = true;
      state.error = null;
    };
    const handleFulfilled = (state, action) => {
      state.loading = false;
      state.entries = action.payload.entries;
      state.total = action.payload.total;
      state.page = action.payload.page;
      state.pageSize = action.payload.page_size;
    };
    const handleRejected = (state, action) => {
      state.loading = false;
      state.error = action.payload;
    };

    builder
      .addCase(fetchGlobalLeaderboard.pending, handlePending)
      .addCase(fetchGlobalLeaderboard.fulfilled, handleFulfilled)
      .addCase(fetchGlobalLeaderboard.rejected, handleRejected)
      .addCase(fetchRegionLeaderboard.pending, handlePending)
      .addCase(fetchRegionLeaderboard.fulfilled, handleFulfilled)
      .addCase(fetchRegionLeaderboard.rejected, handleRejected)
      .addCase(fetchModeLeaderboard.pending, handlePending)
      .addCase(fetchModeLeaderboard.fulfilled, handleFulfilled)
      .addCase(fetchModeLeaderboard.rejected, handleRejected)
      .addCase(fetchRegionModeLeaderboard.pending, handlePending)
      .addCase(fetchRegionModeLeaderboard.fulfilled, handleFulfilled)
      .addCase(fetchRegionModeLeaderboard.rejected, handleRejected);
  },
});

export const { setRegionFilter, setModeFilter, setPage, setPageSize } = leaderboardSlice.actions;
export default leaderboardSlice.reducer;
