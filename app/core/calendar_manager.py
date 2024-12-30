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

    def list_upcoming_events(self, max_results=10):
        now = datetime.utcnow().isoformat() + 'Z'
        events_result = self.service.events().list(
            calendarId='primary', timeMin=now,
            maxResults=max_results, singleEvents=True,
            orderBy='startTime').execute()
        return events_result.get('items', []) 