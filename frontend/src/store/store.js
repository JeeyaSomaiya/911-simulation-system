import { configureStore } from '@reduxjs/toolkit';
import sessionSlice from './slices/sessionSlice';
import uiSlice from './slices/uiSlice';

export const store = configureStore({
  reducer: {
    session: sessionSlice,
    ui: uiSlice,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }),
});
