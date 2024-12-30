from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import base64
import email
from email.mime.text import MIMEText
from datetime import datetime
import os.path
import pickle

class GmailManager:
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.compose'
    ]
    
    def __init__(self):
        self.creds = None
        self.service = None
        self.credentials_path = 'app/config/credentials.json'
        self.token_path = 'gmail_token.pickle'  # Separate token file
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
                    if not os.path.exists(self.credentials_path):
                        raise FileNotFoundError(f"Credentials file not found at {self.credentials_path}")
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, 
                        self.SCOPES
                    )
                    self.creds = flow.run_local_server(
                        port=8081,  # Different port from calendar
                        host='localhost',
                        success_message='Gmail authentication complete!'
                    )
                
                with open(self.token_path, 'wb') as token:
                    pickle.dump(self.creds, token)

            self.service = build('gmail', 'v1', credentials=self.creds)
            print("Gmail authentication successful!")
        
        except Exception as e:
            print(f"Gmail authentication error: {str(e)}")
            raise

    def list_recent_emails(self, max_results=5, query=""):
        """List recent emails with optional search query."""
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            emails = []

            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me', 
                    id=message['id'],
                    format='full'
                ).execute()

                headers = msg['payload']['headers']
                subject = next(h['value'] for h in headers if h['name'] == 'Subject')
                from_email = next(h['value'] for h in headers if h['name'] == 'From')
                date = next(h['value'] for h in headers if h['name'] == 'Date')

                # Get email body
                if 'parts' in msg['payload']:
                    parts = msg['payload']['parts']
                    data = parts[0]['body'].get('data', '')
                else:
                    data = msg['payload']['body'].get('data', '')
                
                if data:
                    text = base64.urlsafe_b64decode(data).decode()
                else:
                    text = "No content"

                emails.append({
                    'id': message['id'],
                    'subject': subject,
                    'from': from_email,
                    'date': date,
                    'snippet': msg['snippet'],
                    'body': text
                })

            return emails

        except Exception as e:
            print(f"Error listing emails: {e}")
            return []

    def send_email(self, to, subject, body):
        """Send an email."""
        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject

            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            self.service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()
            
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    def reply_to_email(self, email_id, body):
        """Reply to a specific email."""
        try:
            # Get the original email
            msg = self.service.users().messages().get(
                userId='me',
                id=email_id,
                format='full'
            ).execute()

            headers = msg['payload']['headers']
            subject = next(h['value'] for h in headers if h['name'] == 'Subject')
            from_email = next(h['value'] for h in headers if h['name'] == 'From')
            
            # Create reply
            if not subject.startswith('Re:'):
                subject = f"Re: {subject}"

            message = MIMEText(body)
            message['to'] = from_email
            message['subject'] = subject
            message['In-Reply-To'] = email_id
            message['References'] = email_id

            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            self.service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()
            
            return True
        except Exception as e:
            print(f"Error replying to email: {e}")
            return False 