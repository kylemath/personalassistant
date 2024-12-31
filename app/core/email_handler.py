from .gmail_manager import GmailManager

class EmailHandler:
    def __init__(self):
        self.gmail = GmailManager()
        self.current_email_context = None
        self.email_knowledge = {}  # Store learned preferences/information
        self.awaiting_answer = None  # Track if waiting for user input
        self.current_draft = None  # Store the current draft
        self.draft_state = None   # Track state of draft process
        self.last_email_list = []  # Store the last list of emails for number references

    def handle_command(self, command: str, args: str) -> str:
        """Handle email-related commands"""
        # Handle draft review responses
        if self.draft_state == "awaiting_review":
            if command.lower() == "send":
                return self._send_current_draft()
            elif command.lower() == "revise":
                self.draft_state = "revising"
                return f"What changes would you like to make to the draft?\n\nPlease respond with: /email revise \"your requested changes\""
            elif command.lower() == "discard":
                self.draft_state = None
                self.current_draft = None
                return "Draft discarded. You can start over with: /email draft reply"

        if command == "revise" and self.draft_state == "revising":
            self.draft_state = "drafting"
            prompt = self._create_revision_prompt(args)
            return prompt

        # Handle answers to AI questions
        if command == "answer" and self.awaiting_answer:
            question = self.awaiting_answer
            self.email_knowledge[question] = args
            self.awaiting_answer = None
            return self._continue_draft_reply()

        if command == "draft" and args == "reply":
            self.draft_state = "drafting"
            if not self.current_email_context:
                return "Please read an email first using /email read <email_id>"
            
            email = self.current_email_context
            
            # Check if we need any information
            missing_info = self._check_missing_information(email)
            if missing_info:
                self.awaiting_answer = missing_info
                return f"To help draft a better reply, could you tell me: {missing_info}\n\nPlease respond with: /email answer \"your response\""

            return self._continue_draft_reply()

        # Existing command handling
        if command == "list":
            return self._handle_list(args)
        elif command == "read":
            return self._handle_read(args)
        elif command == "markread":
            return self._handle_markread(args)
        elif command == "reply":
            return self._handle_reply(args)
        elif command == "starred":
            return self._handle_starred(args)
        else:
            return "Unknown email command. Available commands: list, read, markread, reply, draft reply, starred"

    def _handle_list(self, args: str) -> str:
        """Handle the list command"""
        try:
            max_results = 5  # default
            if args.strip():
                max_results = int(args)
            
            emails = self.gmail.get_unread_emails(max_results)
            if not emails:
                return "No unread emails found."

            # Store the list for number references
            self.last_email_list = emails

            response = "Here are your unread emails:\n\n"
            for i, email in enumerate(emails, 1):
                response += f"{i}. ID: {email['id']}\n"
                response += f"   From: {email['from']}\n"
                response += f"   Subject: {email['subject']}\n"
                response += f"   Date: {email['date']}\n"
                if email['labels']:
                    response += f"   Folder: {', '.join(email['labels'])}\n"
                response += f"   Snippet: {email['snippet']}\n\n"
            
            response += "\nTo read an email, use either:"
            response += "\n- /email read <number> (1-5)"
            response += "\n- /email read <email_id>"
            return response
        except Exception as e:
            return f"Error listing emails: {str(e)}"

    def _handle_read(self, identifier: str) -> str:
        """Handle the read command"""
        try:
            if not identifier:
                return "Please provide an email ID or number. Use /email list to see available emails."
            
            # Check if identifier is a number
            email_id = identifier.strip()
            if email_id.isdigit():
                number = int(email_id)
                if not self.last_email_list or number < 1 or number > len(self.last_email_list):
                    return "Invalid email number. Please use /email list to see available emails."
                email_id = self.last_email_list[number - 1]['id']
            
            email = self.gmail.get_email_by_id(email_id)
            if not email:
                return f"Could not find email with ID {email_id}"

            # Store email context when reading
            self.current_email_context = email

            # Mark as read when viewing
            self.gmail.mark_as_read(email_id)

            response = f"From: {email['from']}\n"
            response += f"Subject: {email['subject']}\n"
            response += f"Date: {email['date']}\n"
            if email.get('labels'):
                response += f"Folder: {', '.join(email['labels'])}\n"
            response += f"\n{email['body']}\n\n"
            response += f"\nTo reply, use either:"
            response += f"\n- /email reply {email_id} \"Your message\""
            response += f"\n- /email draft reply"
            
            return response
        except Exception as e:
            return f"Error reading email: {str(e)}"

    def _handle_markread(self, email_id: str) -> str:
        """Handle the markread command"""
        try:
            if not email_id:
                return "Please provide an email ID."
            
            if self.gmail.mark_as_read(email_id.strip()):
                return f"Email {email_id} marked as read."
            else:
                return f"Failed to mark email {email_id} as read."
        except Exception as e:
            return f"Error marking email as read: {str(e)}"

    def _handle_reply(self, args: str) -> str:
        """Handle the reply command"""
        try:
            parts = args.split(maxsplit=1)
            if len(parts) != 2:
                return "Please provide both email ID and reply message."
            
            email_id, message = parts
            
            if self.gmail.reply_to_email(email_id.strip(), message):
                return f"Reply sent successfully to email {email_id}."
            else:
                return f"Failed to send reply to email {email_id}."
        except Exception as e:
            return f"Error sending reply: {str(e)}" 

    def _check_missing_information(self, email: dict) -> str:
        """Check if we need any additional information to draft a reply."""
        subject = email['subject'].lower()
        
        # Example checks for different types of emails
        if "psych" in subject or "class" in subject:
            if "lecture_recording_policy" not in self.email_knowledge:
                return "What is your policy on recording lectures for your classes?"
            if "syllabus_sharing_policy" not in self.email_knowledge:
                return "What is your policy on sharing syllabi with prospective students?"
        
        if "meeting" in subject or "appointment" in subject:
            if "office_hours" not in self.email_knowledge:
                return "What are your usual office hours or meeting availability?"
        
        return None

    def _create_revision_prompt(self, revision_request: str) -> str:
        """Create prompt for revising the draft."""
        return f"""
Please revise this email draft:

{self.current_draft}

Requested changes:
{revision_request}

Please maintain the professional tone and ensure all original points are still addressed.
"""

    def _send_current_draft(self) -> str:
        """Send the current draft as a reply."""
        if not self.current_draft or not self.current_email_context:
            return "No draft available to send."
        
        try:
            if self.gmail.reply_to_email(self.current_email_context['id'], self.current_draft):
                self.draft_state = None
                self.current_draft = None
                return "Reply sent successfully!"
            return "Failed to send reply."
        except Exception as e:
            return f"Error sending reply: {str(e)}"

    def _continue_draft_reply(self) -> str:
        """Generate the draft reply with available context."""
        email = self.current_email_context
        knowledge = self.email_knowledge

        prompt = f"""
Please help draft a professional reply to this email:

From: {email['from']}
Subject: {email['subject']}
Content: {email['body']}

Additional Context:
{self._format_knowledge()}

The reply should:
1. Address all questions/points in the original email
2. Maintain a professional tone
3. Be clear and concise
4. Include a proper greeting and signature
5. Use the additional context provided when relevant

After the draft, ask if there are any other details I should know to improve future responses.
"""
        return prompt

    def _format_knowledge(self) -> str:
        """Format stored knowledge for the prompt."""
        if not self.email_knowledge:
            return "No additional context available."
        
        return "\n".join(f"- {k}: {v}" for k, v in self.email_knowledge.items()) 

    def set_current_draft(self, draft: str) -> str:
        """Set the current draft and return review options."""
        self.current_draft = draft
        self.draft_state = "awaiting_review"
        
        return f"""
Here's the drafted reply:

{draft}

What would you like to do?
1. /email send - Send this reply
2. /email revise "your requested changes" - Make changes to the draft
3. /email discard - Discard this draft

Or ask any questions about the draft.
""" 

    def _handle_starred(self, args: str) -> str:
        """Handle the starred command"""
        try:
            # If args is "all", get all starred emails
            max_results = None if args.strip().lower() == "all" else 5
            if args.strip() and args.strip().lower() != "all":
                try:
                    max_results = int(args)
                except ValueError:
                    return "Please specify either a number or 'all'"
            
            emails = self.gmail.get_starred_emails(max_results)
            if not emails:
                return "No starred emails found."

            # Store the list for number references
            self.last_email_list = emails

            response = f"Here are your starred emails ({len(emails)} total):\n\n"
            for i, email in enumerate(emails, 1):
                response += f"{i}. ID: {email['id']}\n"
                response += f"   From: {email['from']}\n"
                response += f"   Subject: {email['subject']}\n"
                response += f"   Date: {email['date']}\n"
                if email['labels']:
                    response += f"   Folder: {', '.join(email['labels'])}\n"
                response += f"   Snippet: {email['snippet']}\n\n"
            
            response += "\nTo read an email, use either:"
            response += f"\n- /email read <number> (1-{len(emails)})"
            response += "\n- /email read <email_id>"
            return response
        except Exception as e:
            return f"Error listing starred emails: {str(e)}" 