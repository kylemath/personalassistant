import { configureStore } from '@reduxjs/toolkit';
import chatReducer from './slices/chatSlice';
import calendarReducer from './slices/calendarSlice';

export const store = configureStore({
  reducer: {
    chat: chatReducer,
    calendar: calendarReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch; 