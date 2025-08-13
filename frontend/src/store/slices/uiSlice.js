import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  sidebarOpen: true,
  currentScreen: 'home',
  notifications: [],
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen;
    },
    setCurrentScreen: (state, action) => {
      state.currentScreen = action.payload;
    },
    addNotification: (state, action) => {
      state.notifications.push(action.payload);
    },
    removeNotification: (state, action) => {
      state.notifications = state.notifications.filter(
        (notification) => notification.id !== action.payload
      );
    },
  },
});

export const { toggleSidebar, setCurrentScreen, addNotification, removeNotification } = uiSlice.actions;
export default uiSlice.reducer;
