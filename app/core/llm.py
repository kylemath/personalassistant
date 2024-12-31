from langchain_ollama import OllamaLLM
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from .memory import MemoryManager
from datetime import datetime, timedelta
import json
from .calendar_manager import CalendarManager
from .todo_manager import TodoManager
from .gmail_manager import GmailManager
from .email_handler import EmailHandler
import pytz

class LLMManager:
    def __init__(self):
        callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
        self.llm = OllamaLLM(
            model="mistral:7b-instruct",
            callback_manager=callback_manager,
            temperature=0.7,
        )
        self.memory = MemoryManager()
        self.calendar = CalendarManager()
        self.todos = TodoManager()
        self.gmail = GmailManager()
        self.email_handler = EmailHandler()
        
        # Set timezone and current time context
        self.timezone = 'America/Edmonton'
        self.current_time = datetime.now(pytz.timezone(self.timezone))
        
        # Clean up any duplicate facts
        self.memory.cleanup_duplicates()
        
        # Add timezone facts (add_long_term_fact will now prevent duplicates)
        self.memory.add_long_term_fact(
            f"Current timezone is {self.timezone}",
            "system"
        )
        self.memory.add_long_term_fact(
            f"All times should be interpreted in {self.timezone} timezone",
            "system"
        )

    def _cleanup_timezone_facts(self):
        """Remove duplicate timezone facts."""
        facts = self.memory.list_facts('system')
        seen_facts = set()
        for fact in facts:
            if 'timezone' in fact.lower():
                fact_id = fact.split(']')[0].strip('[')  # Extract fact ID
                if fact in seen_facts:
                    self.memory.delete_fact(fact_id)
                else:
                    seen_facts.add(fact)

    def _ensure_timezone_facts(self):
        """Ensure timezone facts exist, add if missing."""
        facts = self.memory.list_facts('system')
        timezone_fact = f"Current timezone is {self.timezone}"
        interpretation_fact = f"All times should be interpreted in {self.timezone} timezone"
        
        has_timezone = any(timezone_fact in fact for fact in facts)
        has_interpretation = any(interpretation_fact in fact for fact in facts)
        
        if not has_timezone:
            self.memory.add_long_term_fact(timezone_fact, "system")
        if not has_interpretation:
            self.memory.add_long_term_fact(interpretation_fact, "system")

    async def generate_response(self, prompt: str, context: dict = None) -> str:
        try:
            # Update current time on each request
            self.current_time = datetime.now(pytz.timezone(self.timezone))
            
            # Check for calendar intents
            calendar_keywords = [
                "schedule", "appointment", "book", "calendar", "meeting",
                "remind me", "set up", "plan for", "mark down"
            ]
            calendar_query_keywords = [
                "what", "when", "show", "list", "tell me", "do i have",
                "what's", "what is", "what are", "any", "upcoming"
            ]
            time_indicators = ["today", "tomorrow", "tonight", "pm", "am", "next", "on", "at",
                             "this week", "next week", "weekend", "month"]
            
            # Check if this is a calendar query
            if any(keyword in prompt.lower() for keyword in calendar_query_keywords) and \
               any(indicator in prompt.lower() for indicator in time_indicators):
                
                # Get all upcoming events first
                events = self.calendar.list_upcoming_events(max_results=20)  # Get enough events to search through
                
                # If looking for "next" event
                if "next" in prompt.lower():
                    # Parse what we're looking for
                    search_terms = []
                    if "practice" in prompt.lower():
                        search_terms.append("practice")
                    if "game" in prompt.lower():
                        search_terms.append("game")
                    
                    # Add all soccer team calendars
                    if any(team in prompt.lower() for team in ["juventus", "pirates", "beer hunters", "pirates sc"]):
                        if "juventus" in prompt.lower():
                            search_terms.append("juventus")
                        if "pirates" in prompt.lower() or "pirates sc" in prompt.lower():
                            search_terms.append("pirates sc")
                        if "beer" in prompt.lower() or "beer hunters" in prompt.lower():
                            search_terms.append("beer hunters")
                    
                    # Find the next matching event
                    for event in events:
                        summary = event.get('summary', '').lower()
                        calendar = event.get('calendar', '').lower()
                        
                        if any(term in summary.lower() or term in calendar.lower() for term in search_terms):
                            # Convert the datetime to local timezone
                            start_time = event['start'].get('dateTime', event['start'].get('date'))
                            event_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                            local_dt = event_dt.astimezone(pytz.timezone(self.timezone))
                            
                            # Format the date and time naturally
                            day_str = local_dt.strftime('%A')
                            date_str = local_dt.strftime('%B %d')
                            time_str = local_dt.strftime('%I:%M %p').lstrip('0').lower()
                            
                            # Calculate if it's "this" or "next" week
                            today = self.current_time
                            days_until = (local_dt.date() - today.date()).days
                            week_qualifier = "this coming" if days_until < 7 else "next"
                            
                            # Get location if available
                            location = event.get('location', '')
                            location_str = f" at {location}" if location else ""
                            
                            return f"The next {event['summary'].lower()} is {week_qualifier} {day_str}, {date_str} at {time_str}{location_str} [{event.get('calendar', 'Primary')}]"
                    
                    return f"No upcoming {' or '.join(search_terms)} found in the calendar."

                # Determine if query is about tomorrow
                is_tomorrow_query = "tomorrow" in prompt.lower()
                target_date = self.current_time + timedelta(days=1) if is_tomorrow_query else self.current_time
                
                # Ask LLM to convert natural query to calendar list command
                query_prompt = f"""
You are a calendar assistant. TODAY is {self.current_time.strftime('%A, %B %d, %Y')} and the current time is {self.current_time.strftime('%I:%M %p')} {self.timezone}.

Answer this calendar query about {"tomorrow" if is_tomorrow_query else "today"}:
"{prompt}"

Events for {"tomorrow" if is_tomorrow_query else "today"}:
{self._filter_events_by_date(self.calendar.list_upcoming_events(), target_date)}

Rules:
1. ALWAYS start by mentioning today's actual date ({self.current_time.strftime('%A, %B %d, %Y')})
2. When discussing tomorrow, mention it's {target_date.strftime('%A, %B %d, %Y')}
3. Only show events that are actually scheduled for the requested date
4. Format all times in {self.timezone} timezone
5. If no events found for the requested date, explicitly say so
6. Be concise but friendly
7. List events in chronological order

Example response formats:
For today: "Today is Tuesday, December 31, 2024. You have no events scheduled for today."
For tomorrow: "Today is Tuesday, December 31, 2024. For tomorrow (Wednesday, January 1, 2025) you have: Meeting at 2 PM MST"
"""
                response = await self.llm.agenerate([query_prompt])
                return response.generations[0][0].text.strip()

            # Existing calendar creation intent check
            elif any(keyword in prompt.lower() for keyword in calendar_keywords) and \
                 any(indicator in prompt.lower() for indicator in time_indicators):
                
                # Ask LLM to convert natural language to calendar command
                command_prompt = f"""
Convert this calendar request into a /calendar add command:
"{prompt}"

Current time context:
- Current time: {self.current_time.strftime('%I:%M %p, %B %d, %Y')}
- Timezone: {self.timezone}

Rules:
1. Format: /calendar add "Title" "Start Time" "End Time" "Location" "Description"
2. Include all available information from the request
3. Use specific date/time formats with timezone
4. All times should be in {self.timezone}
5. Respond ONLY with the command, no other text

Example:
Request: "Schedule a meeting with John tomorrow at 2pm for 1 hour"
/calendar add "Meeting with John" "2:00 PM MST tomorrow" "3:00 PM MST tomorrow" "" "One hour meeting"
"""
                response = await self.llm.agenerate([command_prompt])
                calendar_command = response.generations[0][0].text.strip()
                
                # Parse the command to show confirmation
                params = self._extract_quoted_params(calendar_command)
                if len(params) >= 2:
                    confirmation = f"""
I'll create this calendar event:
- Title: {params[0]}
- Start: {params[1]}
{f"- End: {params[2]}" if len(params) > 2 else ""}
{f"- Location: {params[3]}" if len(params) > 3 else ""}
{f"- Description: {params[4]}" if len(params) > 4 else ""}

Would you like me to add this event? (Reply with yes/no)
"""
                    # Store the command for later execution
                    self.pending_calendar_command = calendar_command
                    return confirmation
                
                return "I had trouble understanding the calendar details. Please try again."

            # Add a new condition to handle the confirmation response
            elif hasattr(self, 'pending_calendar_command') and prompt.lower() in ['yes', 'y']:
                # Execute the stored command
                command = self.pending_calendar_command
                delattr(self, 'pending_calendar_command')
                return await self._handle_command(command)

            elif hasattr(self, 'pending_calendar_command') and prompt.lower() in ['no', 'n']:
                delattr(self, 'pending_calendar_command')
                return "Calendar event cancelled."

            # Command handling
            if prompt.startswith("/"):
                return await self._handle_command(prompt)

            # Regular chat flow
            conversation_history = self.memory.get_recent_history()
            personal_info = self.memory.get_personal_info()
            relevant_facts = self.memory.get_relevant_facts(prompt)
            
            # Add file context if provided
            file_context = ""
            if context and 'file' in context:
                file_context = f"\nCurrent file: {context['file']}\nContent: {context.get('content', 'Not provided')}"
            
            # Create context-aware prompt with specific instructions about calendar actions
            context_prompt = f"""
You are a helpful AI assistant with access to the following context:

PERSONAL INFORMATION ABOUT THE USER:
{personal_info}

RELEVANT FACTS AND HISTORY:
{relevant_facts}

RECENT CONVERSATION HISTORY:
{conversation_history}{file_context}

Current message: {prompt}

Please respond to the current message while taking into account all available context.
If you learn any new personal information, remember it for future reference.
"""
            response = await self.llm.agenerate([context_prompt])
            response_text = response.generations[0][0].text
            
            # Store the interaction
            self.memory.add_interaction(prompt, response_text)
            
            return response_text
        except Exception as e:
            print(f"Error generating response: {e}")
            return f"Error: {str(e)}"

    async def _handle_command(self, prompt: str) -> str:
        parts = prompt.split()
        command = parts[0].lower()

        if command == "/addfact":
            # Format: /addfact category: fact
            content = " ".join(parts[1:])
            if ":" in content:
                category, fact = content.split(":", 1)
                self.memory.add_long_term_fact(fact.strip(), category.strip())
                return f"Added fact to {category}: {fact}"
            else:
                self.memory.add_long_term_fact(content)
                return f"Added fact: {content}"

        elif command == "/listfacts":
            # Format: /listfacts [category]
            category = parts[1] if len(parts) > 1 else None
            facts = self.memory.list_facts(category)
            if not facts:
                return "No facts found." if category else f"No facts found in category: {category}"
            return "Stored facts:\n" + "\n".join(facts)

        elif command == "/deletefact":
            # Format: /deletefact fact_id
            if len(parts) < 2:
                return "Please provide a fact ID to delete"
            fact_id = parts[1]
            if self.memory.delete_fact(fact_id):
                return f"Deleted fact with ID: {fact_id}"
            return f"Could not find fact with ID: {fact_id}"

        elif command == "/help":
            return "Press the Help (?) button in the bottom right or press 'h' to see all available commands and examples."

        elif command == "/calendar":
            if len(parts) > 1:
                subcommand = parts[1].lower()
                
                if subcommand == "add":
                    # Handle the direct calendar add command
                    try:
                        # Extract the quoted parameters
                        params = self._extract_quoted_params(prompt)
                        if len(params) < 2:
                            return "Please provide at least a title and start time in quotes"
                        
                        summary = params[0]
                        start_time = params[1]
                        end_time = params[2] if len(params) > 2 else None
                        location = params[3] if len(params) > 3 else None
                        description = params[4] if len(params) > 4 else None
                        
                        # Create the event directly
                        event_id = self.calendar.create_event(
                            summary=summary,
                            start_time=start_time,
                            end_time=end_time,
                            location=location,
                            description=description
                        )
                        
                        return f"Successfully created calendar event: {summary}\nUse /calendar list to verify."
                    except Exception as e:
                        return f"Error creating calendar event: {str(e)}"
                        
                elif subcommand == "list":
                    # Get optional number of events parameter
                    max_results = 10  # default
                    if len(parts) > 2:
                        try:
                            max_results = int(parts[2])
                        except ValueError:
                            return "Please provide a valid number for the amount of events to show"
                    
                    events = self.calendar.list_upcoming_events(max_results)
                    if not events:
                        return "No upcoming events found."
                    
                    response = f"Next {len(events)} upcoming events:\n" + "\n".join(
                        f"- {event['summary']} ({event['start'].get('dateTime', event['start'].get('date'))}) [{event.get('calendar', 'Primary')}]"
                        for event in events
                    )
                    
                    if len(events) == max_results:
                        response += f"\n\nTo see more events, use: /calendar list <number>"
                    
                    return response

        elif command == "/todo":
            subcommand = parts[1] if len(parts) > 1 else "list"
            
            if subcommand == "add":
                # Format: /todo add "Task description" --priority high --category work --due "next friday"
                try:
                    params = self._extract_quoted_params(prompt)
                    if not params:
                        return "Please provide a task description in quotes"
                    
                    task = params[0]
                    priority = "medium"
                    category = "general"
                    due_date = None
                    notes = params[1] if len(params) > 1 else None
                    
                    # Parse flags
                    if "--priority" in prompt:
                        for p in ["high", "medium", "low"]:
                            if p in prompt.lower():
                                priority = p
                                break
                    
                    if "--category" in prompt:
                        cat_start = prompt.find("--category") + 10
                        cat_end = prompt.find("--", cat_start) if "--" in prompt[cat_start:] else None
                        category = prompt[cat_start:cat_end].strip() if cat_end else prompt[cat_start:].strip()
                    
                    if "--due" in prompt:
                        due_start = prompt.find("--due") + 5
                        due_end = prompt.find("--", due_start) if "--" in prompt[due_start:] else None
                        due_str = prompt[due_start:due_end].strip() if due_end else prompt[due_start:].strip()
                        due_date = self.calendar.parse_time(due_str).isoformat()
                    
                    todo_id = self.todos.add_todo(task, priority, category, due_date, notes)
                    return f"Added todo: {task} (ID: {todo_id})"
                
                except Exception as e:
                    return f"Error adding todo: {str(e)}"
            
            elif subcommand == "list":
                # Format: /todo list [category] [--priority high/medium/low]
                category = parts[2] if len(parts) > 2 and not parts[2].startswith("--") else None
                priority = None
                if "--priority" in prompt:
                    for p in ["high", "medium", "low"]:
                        if p in prompt.lower():
                            priority = p
                            break
                
                todos = self.todos.list_todos(category=category, priority=priority)
                if not todos:
                    return "No todos found."
                
                return "Todo List:\n" + "\n".join(
                    f"[{todo['id']}] ({todo['priority']}) {todo['task']}" +
                    (f" - Due: {todo['due_date']}" if todo['due_date'] else "") +
                    (f" - Category: {todo['category']}" if todo['category'] != "general" else "")
                    for todo in todos
                )
            
            elif subcommand == "done":
                # Format: /todo done <todo_id>
                if len(parts) < 3:
                    return "Please provide a todo ID"
                todo_id = parts[2]
                if self.todos.complete_todo(todo_id):
                    return f"Marked todo {todo_id} as completed"
                return f"Could not find todo with ID: {todo_id}"
            
            elif subcommand == "delete":
                # Format: /todo delete <todo_id>
                if len(parts) < 3:
                    return "Please provide a todo ID"
                todo_id = parts[2]
                if self.todos.delete_todo(todo_id):
                    return f"Deleted todo {todo_id}"
                return f"Could not find todo with ID: {todo_id}"

        elif command == "/email":
            if len(parts) < 2:
                return "Please provide an email command. Available commands: list, read, markread, reply, draft reply, answer, send, revise, discard"
            
            subcommand = parts[1]
            args = " ".join(parts[2:]) if len(parts) > 2 else ""
            response = self.email_handler.handle_command(subcommand, args)
            
            # Handle different types of responses
            if subcommand in ["draft", "answer", "revise"]:
                if "could you tell me:" in response.lower():
                    return response  # Return the question to the user
                if "What would you like to do?" in response:
                    return response  # Return the review options
                # Generate new draft
                draft_response = await self.generate_response(response, {"type": "email_draft"})
                return self.email_handler.set_current_draft(draft_response)
            
            return response

        return f"Unknown command: {command}" 

    def _extract_quoted_params(self, text: str) -> list:
        """Extract parameters enclosed in quotes."""
        import re
        return re.findall(r'"([^"]*)"', text) 

    def _filter_events_by_date(self, events, target_date):
        """Filter events to only include those on the specified date."""
        filtered = []
        target_date = target_date.date()
        
        for event in events:
            event_time = event.get('start', {}).get('dateTime')
            event_date = event.get('start', {}).get('date')
            
            if event_time:
                # Convert to timezone-aware datetime
                event_datetime = datetime.fromisoformat(event_time.replace('Z', '+00:00'))
                event_datetime = event_datetime.astimezone(pytz.timezone(self.timezone))
                if event_datetime.date() == target_date:
                    filtered.append(event)
            elif event_date and datetime.fromisoformat(event_date).date() == target_date:
                filtered.append(event)
        
        return filtered 
 