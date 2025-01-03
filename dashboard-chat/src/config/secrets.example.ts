export const CALENDAR_NAMES = {
  PERSONAL: 'your.personal@gmail.com',
  WORK: 'your.work@company.com',
  TALKS: 'talks@example.com',
  HOLIDAYS: 'holidays@example.com',
  PIRATES: 'pirates@example.com',
  BEER_HUNTERS: 'beerhunters@example.com',
  SHARED: 'shared@example.com'
} as const;

export const CALENDAR_COLORS = {
  [CALENDAR_NAMES.PERSONAL]: '#007bff',    // Blue
  [CALENDAR_NAMES.WORK]: '#28a745',        // Green
  [CALENDAR_NAMES.TALKS]: '#dc3545',       // Red
  [CALENDAR_NAMES.HOLIDAYS]: '#dc3545',    // Red
  [CALENDAR_NAMES.PIRATES]: '#89CFF0',     // Baby Blue
  [CALENDAR_NAMES.BEER_HUNTERS]: '#ffc107', // Yellow
  [CALENDAR_NAMES.SHARED]: '#20c997'       // Teal
} as const;

// Default visibility settings for calendars
export const CALENDAR_VISIBILITY = {
  [CALENDAR_NAMES.PERSONAL]: true,      // Show by default
  [CALENDAR_NAMES.WORK]: false,         // Hidden by default
  [CALENDAR_NAMES.TALKS]: false,        // Hidden by default
  [CALENDAR_NAMES.HOLIDAYS]: false,     // Hidden by default
  [CALENDAR_NAMES.PIRATES]: true,       // Show by default
  [CALENDAR_NAMES.BEER_HUNTERS]: true,  // Show by default
  [CALENDAR_NAMES.SHARED]: false        // Hidden by default
} as const;

// Google Maps API key (get from Google Cloud Console)
export const GOOGLE_MAPS_API_KEY = 'YOUR_GOOGLE_MAPS_API_KEY';

// Other API keys or sensitive configuration
export const API_CONFIG = {
  BASE_URL: 'http://localhost:8000',
  WS_URL: 'ws://localhost:8000/ws'
}; 