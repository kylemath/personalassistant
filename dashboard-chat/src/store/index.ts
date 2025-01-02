import { configureStore } from '@reduxjs/toolkit';
import chatReducer, { ChatState } from './slices/chatSlice';

export interface RootState {
  chat: ChatState;
}

export const store = configureStore({
  reducer: {
    chat: chatReducer,
  },
});

export type AppDispatch = typeof store.dispatch; 