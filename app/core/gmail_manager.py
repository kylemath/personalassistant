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
import requests
from urllib.parse import urlparse
import re

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
            print("Debug: Starting Gmail authentication")
            if os.path.exists(self.token_path):
                print("Debug: Found existing token file")
                with open(self.token_path, 'rb') as token:
                    self.creds = pickle.load(token)
                print("Debug: Loaded credentials from token file")
            
            if not self.creds or not self.creds.valid:
                print("Debug: Credentials invalid or missing")
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    print("Debug: Refreshing expired credentials")
                    self.creds.refresh(Request())
                else:
                    print("Debug: Checking for credentials file")
                    if not os.path.exists(self.credentials_path):
                        raise FileNotFoundError(f"Credentials file not found at {self.credentials_path}")
                    
                    print("Debug: Starting OAuth flow")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, 
                        self.SCOPES
                    )
                    self.creds = flow.run_local_server(
                        port=8081,  # Different port from calendar
                        host='localhost',
                        success_message='Gmail authentication complete!'
                    )
                    print("Debug: OAuth flow completed")
                
                print("Debug: Saving new token")
                with open(self.token_path, 'wb') as token:
                    pickle.dump(self.creds, token)

            print("Debug: Building Gmail service")
            self.service = build('gmail', 'v1', credentials=self.creds)
            print("Gmail authentication successful!")
        
        except Exception as e:
            print(f"Gmail authentication error: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise

    def list_recent_emails(self, max_results=10, query=""):
        """List recent emails from the inbox.
        
        Args:
            max_results (int): Maximum number of emails to return
            query (str): Optional query string to filter emails
            
        Returns:
            list: List of email dictionaries containing id, from, subject, date, snippet
        """
        try:
            print("Debug: Fetching recent emails")
            # Prepare the query
            search_query = 'in:inbox ' + query
            
            # Get message list
            results = self.service.users().messages().list(
                userId='me',
                maxResults=max_results,
                q=search_query
            ).execute()
            
            messages = results.get('messages', [])
            print(f"Debug: Found {len(messages)} messages")
            
            emails = []
            for msg in messages:
                # Get full message details
                message = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()
                
                headers = message['payload']['headers']
                email_data = {
                    'id': message['id'],
                    'from': next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown'),
                    'subject': next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject'),
                    'date': next((h['value'] for h in headers if h['name'] == 'Date'), ''),
                    'snippet': message.get('snippet', ''),
                    'labels': message.get('labelIds', [])
                }
                emails.append(email_data)
            
            print(f"Debug: Processed {len(emails)} emails")
            return emails
            
        except Exception as e:
            print(f"Error listing recent emails: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
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

    def star_email(self, email_id):
        """Star an email by adding the STARRED label."""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'addLabelIds': ['STARRED']}
            ).execute()
            return True
        except Exception as e:
            print(f"Error starring email: {e}")
            return False

    def unstar_email(self, email_id):
        """Unstar an email by removing the STARRED label."""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['STARRED']}
            ).execute()
            return True
        except Exception as e:
            print(f"Error unstarring email: {e}")
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
                    label_names = ['STARRED']  # Always include STARRED label
                    label_list = self.service.users().labels().list(userId='me').execute()
                    for label_id in labels:
                        for label in label_list['labels']:
                            if label['id'] == label_id:
                                # Include UNREAD label if present
                                if label['id'] == 'UNREAD':
                                    label_names.append('UNREAD')
                                # Include other non-system labels
                                elif label['id'] not in ['STARRED', 'CATEGORY_PERSONAL', 'IMPORTANT']:
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

    def list_unread_emails(self, max_results=5):
        """List unread emails from INBOX only."""
        try:
            print("Debug: Starting list_unread_emails")
            unread_emails = []
            page_token = None
            
            while True:
                # Build request parameters with INBOX filter
                params = {
                    'userId': 'me',
                    'q': 'is:unread in:inbox',  # Add in:inbox to query
                    'labelIds': ['INBOX']  # Also specify INBOX label
                }
                if max_results:
                    params['maxResults'] = max_results
                if page_token:
                    params['pageToken'] = page_token

                print(f"Debug: Requesting emails with params: {params}")
                results = self.service.users().messages().list(**params).execute()
                messages = results.get('messages', [])
                
                if not messages:
                    print("Debug: No unread messages found in response")
                    break
                
                print(f"Debug: Found {len(messages)} messages")
                # Process messages in this page
                for message in messages:
                    try:
                        msg = self.service.users().messages().get(
                            userId='me', 
                            id=message['id'],
                            format='full'
                        ).execute()

                        headers = msg['payload']['headers']
                        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                        from_email = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                        date = next((h['value'] for h in headers if h['name'] == 'Date'), '')

                        # Get labels (like in starred emails)
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

                        unread_emails.append({
                            'id': message['id'],
                            'subject': subject,
                            'from': from_email,
                            'date': date,
                            'snippet': msg['snippet'],
                            'labels': label_names
                        })
                        
                    except Exception as e:
                        print(f"Error processing message {message['id']}: {e}")
                        continue

                # Check if we should stop
                if max_results and len(unread_emails) >= max_results:
                    unread_emails = unread_emails[:max_results]
                    break
                    
                # Get next page token
                page_token = results.get('nextPageToken')
                if not page_token:
                    break

            print(f"Debug: Found {len(unread_emails)} unread emails")
            return unread_emails
            
        except Exception as e:
            print(f"Error listing unread emails: {e}")
            return [] 

    def get_unsubscribe_link(self, email_id: str) -> str:
        """Get unsubscribe link from email headers if available."""
        try:
            # Get full message to access headers
            message = self.service.users().messages().get(
                userId='me',
                id=email_id,
                format='full'
            ).execute()
            
            headers = message['payload']['headers']
            
            # Check List-Unsubscribe header
            unsubscribe = next(
                (h['value'] for h in headers if h['name'].lower() == 'list-unsubscribe'),
                None
            )
            
            if unsubscribe:
                # Extract URL from <> brackets if present
                if '<' in unsubscribe and '>' in unsubscribe:
                    return unsubscribe[unsubscribe.find('<')+1:unsubscribe.find('>')]
                return unsubscribe
            
            return None
            
        except Exception as e:
            print(f"Error getting unsubscribe link: {e}")
            return None 

    def unsubscribe_from_sender(self, email_id: str) -> str:
        """Attempt to automatically unsubscribe from sender."""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=email_id,
                format='full'
            ).execute()
            
            # First check List-Unsubscribe header
            headers = message['payload']['headers']
            header_unsubscribe = next(
                (h['value'] for h in headers if h['name'].lower() == 'list-unsubscribe'),
                None
            )
            
            # Then check email body for unsubscribe links
            body_unsubscribe = None
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/html':
                        body = base64.urlsafe_b64decode(part['body']['data']).decode()
                        # Look for unsubscribe link in HTML
                        unsubscribe_match = re.search(r'href="([^"]*unsubscribe[^"]*)"', body, re.IGNORECASE)
                        if unsubscribe_match:
                            body_unsubscribe = unsubscribe_match.group(1)
                            break
            
            # Try body unsubscribe link first (usually more reliable)
            if body_unsubscribe:
                print(f"Debug: Found unsubscribe link in email body: {body_unsubscribe}")
                return self._handle_http_unsubscribe(body_unsubscribe)
            
            # Fall back to header if no body link found
            if header_unsubscribe:
                http_match = re.search(r'https?://[^\s<>]+', header_unsubscribe)
                if http_match:
                    url = http_match.group(0)
                    print(f"Debug: Found HTTP unsubscribe URL in header: {url}")
                    return self._handle_http_unsubscribe(url)
                    
                mailto_match = re.search(r'mailto:([^\s<>]+)', header_unsubscribe)
                if mailto_match:
                    email = mailto_match.group(1)
                    print(f"Debug: Found mailto unsubscribe in header: {email}")
                    return self._handle_mailto_unsubscribe(email)
            
            return "No unsubscribe link found in email"
            
        except Exception as e:
            return f"Error attempting to unsubscribe: {str(e)}"

    def _get_unsubscribe_info(self, email_id: str) -> dict:
        """Get detailed unsubscribe information from email."""
        message = self.service.users().messages().get(
            userId='me',
            id=email_id,
            format='full'
        ).execute()
        
        headers = message['payload']['headers']
        unsubscribe = next(
            (h['value'] for h in headers if h['name'].lower() == 'list-unsubscribe'),
            None
        )
        
        if not unsubscribe:
            return None
        
        # Parse mailto: links
        if 'mailto:' in unsubscribe:
            mailto = re.search(r'mailto:([^\s>]+)', unsubscribe)
            if mailto:
                return {
                    'method': 'mailto',
                    'data': mailto.group(1)
                }
            
        # Parse HTTP links
        if 'http' in unsubscribe:
            http = re.search(r'https?://[^\s>]+', unsubscribe)
            if http:
                return {
                    'method': 'http',
                    'data': http.group(0)
                }
        
        return None

    def _handle_mailto_unsubscribe(self, email: str) -> str:
        """Handle mailto: unsubscribe by sending an email."""
        try:
            # Create email message
            message = {
                'raw': self._create_unsubscribe_email(email)
            }
            
            # Send the unsubscribe email
            self.service.users().messages().send(
                userId='me',
                body=message
            ).execute()
            
            return f"Sent unsubscribe email to {email}"
            
        except Exception as e:
            return f"Failed to send unsubscribe email: {str(e)}"

    def _handle_http_unsubscribe(self, url: str) -> str:
        """Handle HTTP unsubscribe by making a GET request."""
        try:
            # Safety check for URL
            parsed = urlparse(url)
            if not parsed.scheme in ['http', 'https']:
                return f"Invalid unsubscribe URL: {url}"
            
            print(f"Debug: Attempting to access unsubscribe URL: {url}")
            # Make the request
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return f"Successfully accessed unsubscribe URL: {url}\nPlease check your email for confirmation."
            else:
                return f"Error accessing unsubscribe URL (status code: {response.status_code})\nURL: {url}"
            
        except Exception as e:
            return f"Failed to access unsubscribe URL: {url}\nError: {str(e)}"

    def get_email(self, email_id: str) -> dict:
        """Get full email content by ID."""
        try:
            # Get the full message
            message = self.service.users().messages().get(
                userId='me',
                id=email_id,
                format='full'
            ).execute()
            
            # Extract headers
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            from_email = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Get labels
            labels = self.service.users().messages().get(
                userId='me',
                id=email_id,
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
            
            # Extract body
            body = ''
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        body = base64.urlsafe_b64decode(part['body']['data']).decode()
                        break
            else:
                # Handle messages without parts
                if 'data' in message['payload']['body']:
                    body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode()
            
            return {
                'id': email_id,
                'subject': subject,
                'from': from_email,
                'date': date,
                'body': body,
                'labels': label_names,
                'snippet': message.get('snippet', '')
            }
            
        except Exception as e:
            print(f"Error getting email: {e}")
            return None

    def _create_unsubscribe_email(self, to_email: str) -> str:
        """Create an unsubscribe email message."""
        try:
            message = MIMEText('')  # Empty body
            message['to'] = to_email
            message['subject'] = 'Unsubscribe'
            
            # Convert to base64 URL-safe string
            raw = base64.urlsafe_b64encode(message.as_bytes())
            return raw.decode()
            
        except Exception as e:
            print(f"Error creating unsubscribe email: {e}")
            raise