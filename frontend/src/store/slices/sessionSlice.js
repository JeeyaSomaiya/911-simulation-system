import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  currentSession: null,
  isLoading: false,
  error: null,
  conversation: [],
};

const sessionSlice = createSlice({
  name: 'session',
  initialState,
  reducers: {
    setLoading: (state, action) => {
      state.isLoading = action.payload;
    },
    setSession: (state, action) => {
      state.currentSession = action.payload;
      state.error = null;
    },
    setError: (state, action) => {
      state.error = action.payload;
      state.isLoading = false;
    },
    addMessage: (state, action) => {
      state.conversation.push(action.payload);
    },
    clearSession: (state) => {
      state.currentSession = null;
      state.conversation = [];
      state.error = null;
    },
  },
});

export const { setLoading, setSession, setError, addMessage, clearSession } = sessionSlice.actions;
export default sessionSlice.reducer;
