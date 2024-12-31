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
            
            # Get thread headers from original email
            message_id = next((h['value'] for h in headers if h['name'] == 'Message-ID'), None)
            references = next((h['value'] for h in headers if h['name'] == 'References'), '')
            
            # Create reply
            if not subject.startswith('Re:'):
                subject = f"Re: {subject}"

            message = MIMEText(body)
            message['to'] = from_email
            message['subject'] = subject
            
            # Add threading headers
            if message_id:
                message['In-Reply-To'] = message_id
                message['References'] = f"{references} {message_id}".strip()
            
            # Add thread ID to ensure Gmail groups the messages
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            self.service.users().messages().send(
                userId='me',
                body={
                    'raw': raw,
                    'threadId': msg['threadId']  # Add thread ID to keep conversation together
                }
            ).execute()
            
            return True
        except Exception as e:
            print(f"Error replying to email: {e}")
            return False 

    def get_unread_emails(self, max_results=5):
        """Get only unread emails."""
        try:
            # Query for unread emails using Gmail's search syntax
            # Only show unread emails that are in inbox and not in excluded categories
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread in:inbox -category:updates -category:promotions -category:forums',
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            unread_emails = []

            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me', 
                    id=message['id'],
                    format='full'
                ).execute()

                # Get labels first to check if we should process this email
                labels = self.service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='metadata',
                    metadataHeaders=['labelIds']
                ).execute().get('labelIds', [])

                # Skip if it's in any of the excluded categories
                if any(label in labels for label in ['CATEGORY_UPDATES', 'CATEGORY_PROMOTIONS', 'CATEGORY_FORUMS']):
                    continue

                # Skip if not in inbox (archived)
                if 'INBOX' not in labels:
                    continue

                headers = msg['payload']['headers']
                subject = next(h['value'] for h in headers if h['name'] == 'Subject')
                from_email = next(h['value'] for h in headers if h['name'] == 'From')
                date = next(h['value'] for h in headers if h['name'] == 'Date')

                # Convert label IDs to names
                label_names = []
                label_list = self.service.users().labels().list(userId='me').execute()
                for label_id in labels:
                    for label in label_list['labels']:
                        if label['id'] == label_id:
                            # Skip some system labels
                            if label['id'] not in ['UNREAD', 'CATEGORY_PERSONAL', 'IMPORTANT']:
                                label_names.append(label['name'])

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

                unread_emails.append({
                    'id': message['id'],
                    'subject': subject,
                    'from': from_email,
                    'date': date,
                    'snippet': msg['snippet'],
                    'body': text,
                    'labels': label_names
                })

            return unread_emails

        except Exception as e:
            print(f"Error listing unread emails: {e}")
            return []

    def mark_as_read(self, email_id):
        """Mark an email as read by removing the UNREAD label."""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except Exception as e:
            print(f"Error marking email as read: {e}")
            return False

    def process_new_emails(self, handler_function, max_results=5):
        """Process new unread emails with a handler function.
        
        Args:
            handler_function: Function that takes an email dict and returns a reply message
                            if a reply is needed (or None if no reply is needed)
            max_results: Maximum number of unread emails to process
        """
        unread_emails = self.get_unread_emails(max_results)
        
        for email in unread_emails:
            # Process email with handler function
            reply_message = handler_function(email)
            
            if reply_message:
                # Send reply if handler returned a message
                self.reply_to_email(email['id'], reply_message)
            
            # Mark as read after processing
            self.mark_as_read(email['id']) 

    def get_email_by_id(self, email_id: str) -> dict:
        """Get a specific email by ID."""
        try:
            msg = self.service.users().messages().get(
                userId='me', 
                id=email_id,
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

            return {
                'id': msg['id'],
                'subject': subject,
                'from': from_email,
                'date': date,
                'snippet': msg['snippet'],
                'body': text
            }

        except Exception as e:
            print(f"Error getting email: {e}")
            return None 

    def get_starred_emails(self, max_results=None):
        """Get starred emails. If max_results is None, get all starred emails."""
        try:
            starred_emails = []
            page_token = None
            
            while True:
                # Build request parameters
                params = {
                    'userId': 'me',
                    'q': 'is:starred',
                }
                if max_results:
                    params['maxResults'] = max_results
                if page_token:
                    params['pageToken'] = page_token

                # Get page of results
                results = self.service.users().messages().list(**params).execute()
                messages = results.get('messages', [])
                
                # Process messages in this page
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

                    # Get labels
                    labels = self.service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='metadata',
                        metadataHeaders=['labelIds']
                    ).execute().get('labelIds', [])

                    # Convert label IDs to names
                    label_names = []
                    label_list = self.service.users().labels().list(userId='me').execute()
                    for label_id in labels:
                        for label in label_list['labels']:
                            if label['id'] == label_id:
                                if label['id'] not in ['STARRED', 'UNREAD', 'CATEGORY_PERSONAL', 'IMPORTANT']:
                                    label_names.append(label['name'])

                    starred_emails.append({
                        'id': message['id'],
                        'subject': subject,
                        'from': from_email,
                        'date': date,
                        'snippet': msg['snippet'],
                        'labels': label_names
                    })

                # Check if we should stop
                if max_results and len(starred_emails) >= max_results:
                    starred_emails = starred_emails[:max_results]
                    break
                    
                # Get next page token
                page_token = results.get('nextPageToken')
                if not page_token:
                    break

            return starred_emails

        except Exception as e:
            print(f"Error listing starred emails: {e}")
            return [] 