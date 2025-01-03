import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface Email {
  id: string;
  from: string;
  subject: string;
  date: string;
  snippet: string;
  labels: string[];
}

interface EmailState {
  emails: Email[];
  starredEmails: Email[];
  loading: boolean;
  error: string | null;
}

const initialState: EmailState = {
  emails: [],
  starredEmails: [],
  loading: false,
  error: null
};

const emailSlice = createSlice({
  name: 'email',
  initialState,
  reducers: {
    setEmails: (state, action: PayloadAction<Email[]>) => {
      state.emails = action.payload;
    },
    setStarredEmails: (state, action: PayloadAction<Email[]>) => {
      state.starredEmails = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    markEmailAsRead: (state, action: PayloadAction<string>) => {
      const email = state.emails.find(e => e.id === action.payload);
      if (email) {
        email.labels = email.labels.filter(label => label !== 'UNREAD');
      }
      // Also update in starred emails if present
      const starredEmail = state.starredEmails.find(e => e.id === action.payload);
      if (starredEmail) {
        starredEmail.labels = starredEmail.labels.filter(label => label !== 'UNREAD');
      }
    },
    toggleEmailStar: (state, action: PayloadAction<string>) => {
      const updateEmailLabels = (email: Email | undefined) => {
        if (email) {
          if (email.labels.includes('STARRED')) {
            email.labels = email.labels.filter(label => label !== 'STARRED');
          } else {
            email.labels.push('STARRED');
          }
        }
      };

      // Update in both lists
      updateEmailLabels(state.emails.find(e => e.id === action.payload));
      updateEmailLabels(state.starredEmails.find(e => e.id === action.payload));
    }
  }
});

export const { setEmails, setStarredEmails, setLoading, setError, markEmailAsRead, toggleEmailStar } = emailSlice.actions;
export default emailSlice.reducer; 