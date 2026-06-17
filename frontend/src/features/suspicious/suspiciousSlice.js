import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { getSuspiciousPlayers } from '../../services/suspiciousApi';

export const fetchSuspiciousPlayers = createAsyncThunk(
  'suspicious/fetchAll',
  async (_, { rejectWithValue }) => {
    try {
      return await getSuspiciousPlayers();
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

const suspiciousSlice = createSlice({
  name: 'suspicious',
  initialState: {
    entries: [],
    total: 0,
    loading: false,
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchSuspiciousPlayers.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchSuspiciousPlayers.fulfilled, (state, action) => {
        state.loading = false;
        state.entries = action.payload.entries;
        state.total = action.payload.total;
      })
      .addCase(fetchSuspiciousPlayers.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export default suspiciousSlice.reducer;
