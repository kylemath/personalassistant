from langchain_ollama import OllamaLLM
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from .memory import MemoryManager
from datetime import datetime
from .calendar_manager import CalendarManager
from .todo_manager import TodoManager
from .gmail_manager import GmailManager
from .email_handler import EmailHandler

class LLMManager:
    def __init__(self):
        callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
        self.llm = OllamaLLM(
            model="mistral:7b-instruct",
            callback_manager=callback_manager,
            temperature=0.7,
        )
        self.memory = MemoryManager()
        self.calendar = CalendarManager()  # Re-enable calendar
        self.todos = TodoManager()
        self.gmail = GmailManager()
        self.email_handler = EmailHandler()

    async def generate_response(self, prompt: str, context: dict = None) -> str:
        try:
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
            
            # Create context-aware prompt
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
            subcommand = parts[1] if len(parts) > 1 else "list"
            
            if subcommand == "add":
                try:
                    # Extract quoted parameters
                    params = self._extract_quoted_params(prompt)
                    if len(params) < 2:
                        return "Please provide at least a title and start time in quotes"
                    
                    summary = params[0]
                    start_time = params[1]
                    end_time = params[2] if len(params) > 2 else None
                    description = params[3] if len(params) > 3 else None
                    location = params[4] if len(params) > 4 else None
                    
                    # Check for recurrence flag
                    recurrence = None
                    if "--recurring" in prompt.lower():
                        for pattern in ["daily", "weekly", "monthly", "yearly"]:
                            if pattern in prompt.lower():
                                recurrence = pattern
                                break
                    
                    event_id = self.calendar.create_event(
                        summary=summary,
                        start_time=start_time,
                        end_time=end_time,
                        description=description,
                        location=location,
                        recurrence=recurrence
                    )
                    
                    recurrence_msg = f" ({recurrence})" if recurrence else ""
                    return f"Created calendar event: {summary}{recurrence_msg} (ID: {event_id})"
                except Exception as e:
                    return f"Error creating event: {str(e)}"
            
            elif subcommand == "list":
                events = self.calendar.list_upcoming_events()
                if not events:
                    return "No upcoming events found."
                
                return "Upcoming events:\n" + "\n".join(
                    f"- {event['summary']} ({event['start'].get('dateTime', event['start'].get('date'))})"
                    for event in events
                )

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