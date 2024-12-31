from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
import pickle
from datetime import datetime, timedelta
from dateparser import parse
from typing import Optional, Dict, Any
import pytz

class CalendarManager:
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    RECURRENCE_PATTERNS = {
        'daily': 'RRULE:FREQ=DAILY',
        'weekly': 'RRULE:FREQ=WEEKLY',
        'monthly': 'RRULE:FREQ=MONTHLY',
        'yearly': 'RRULE:FREQ=YEARLY'
    }
    
    def __init__(self):
        self.creds = None
        self.service = None
        self.credentials_path = 'app/config/credentials.json'
        self.token_path = 'calendar_token.pickle'  # Separate token file
        self._authenticate()
        
        # Add additional calendars
        self.additional_calendars = {
            "Soccer": "https://calendar.sportsyou.com/access/us-7e6fe0f1-8b2a-4e8d-b27b-686b1b8cb400/7bf5e873-2f8c-4d60-b0b5-390b06f89cbf"
        }

    def _authenticate(self):
        try:
            if os.path.exists(self.token_path):
                with open(self.token_path, 'rb') as token:
                    self.creds = pickle.load(token)
            
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, 
                        self.SCOPES
                    )
                    self.creds = flow.run_local_server(
                        port=8080,
                        host='localhost',
                        success_message='Calendar authentication complete!'
                    )
                
                with open(self.token_path, 'wb') as token:
                    pickle.dump(self.creds, token)

            self.service = build('calendar', 'v3', credentials=self.creds)
            print("Calendar authentication successful!")
        
        except Exception as e:
            print(f"Calendar authentication error: {str(e)}")
            raise

    def parse_time(self, time_str: str, reference_date: datetime = None) -> datetime:
        """Parse natural language time strings."""
        parsed = parse(time_str, settings={
            'PREFER_DATES_FROM': 'future',
            'RELATIVE_BASE': reference_date or datetime.now()
        })
        if not parsed:
            raise ValueError(f"Could not parse time string: {time_str}")
        return parsed

    def create_event(self, 
                    summary: str, 
                    start_time: str, 
                    end_time: Optional[str] = None, 
                    description: Optional[str] = None, 
                    location: Optional[str] = None,
                    recurrence: Optional[str] = None,
                    timezone: str = 'America/New_York') -> str:
        """Create a calendar event with natural language time parsing and recurrence."""
        try:
            # Parse start time
            start = self.parse_time(start_time)
            
            # If no end time specified, default to 1 hour
            if not end_time:
                end = start + timedelta(hours=1)
            else:
                end = self.parse_time(end_time)

            # Create event body
            event = {
                'summary': summary,
                'location': location,
                'description': description,
                'start': {
                    'dateTime': start.isoformat(),
                    'timeZone': timezone,
                },
                'end': {
                    'dateTime': end.isoformat(),
                    'timeZone': timezone,
                },
            }

            # Add recurrence if specified
            if recurrence:
                recurrence_rule = self.RECURRENCE_PATTERNS.get(recurrence.lower())
                if recurrence_rule:
                    event['recurrence'] = [recurrence_rule]
                else:
                    raise ValueError(f"Invalid recurrence pattern: {recurrence}")

            created_event = self.service.events().insert(calendarId='primary', body=event).execute()
            return created_event['id']

        except Exception as e:
            raise Exception(f"Failed to create event: {str(e)}")

    def _get_google_events(self, max_results=10):
        """Get events from all accessible Google calendars."""
        now = datetime.utcnow().isoformat() + 'Z'
        all_events = []
        
        # Calendars to exclude
        excluded_calendars = ['Weather', 'Holidays in United States', 'Jewish Holidays', 'Edmonton Oilers']

        try:
            # First, get list of all calendar IDs
            calendar_list = self.service.calendarList().list().execute()
            
            # Fetch events from each calendar
            for calendar_entry in calendar_list['items']:
                cal_id = calendar_entry['id']
                cal_name = calendar_entry['summary']
                
                # Skip excluded calendars
                if cal_name in excluded_calendars:
                    continue
                    
                try:
                    # Get events from each calendar (don't limit here)
                    events_result = self.service.events().list(
                        calendarId=cal_id,
                        timeMin=now,
                        maxResults=100,  # Get more events to ensure we have enough after merging
                        singleEvents=True,
                        orderBy='startTime'
                    ).execute()
                    
                    # Add calendar source to each event
                    for event in events_result.get('items', []):
                        if 'summary' not in event:
                            event['summary'] = 'Untitled Event'
                        event['calendar'] = cal_name
                        all_events.append(event)
                        
                except Exception as e:
                    print(f"Error fetching events from calendar {cal_name}: {e}")
                    continue
                    
            return all_events
        
        except Exception as e:
            print(f"Error listing calendars: {e}")
            return []

    def list_upcoming_events(self, max_results=10):
        """List upcoming events from all calendars."""
        try:
            # Get all events first
            events = self._get_google_events(max_results)
            
            # Sort all events
            def event_sort_key(event):
                start = event.get('start', {})
                return start.get('dateTime') or start.get('date') or ''
            
            # Sort and limit only at the end
            sorted_events = sorted(events, key=event_sort_key)
            return sorted_events[:max_results]  # Apply limit here
            
        except Exception as e:
            print(f"Error in list_upcoming_events: {e}")
            return []