import requests
import argparse
import json
import os
from rich.console import Console
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.panel import Panel
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

console = Console()

def load_commands():
    """Load commands from commands.json."""
    try:
        commands_path = os.path.join('app', 'config', 'commands.json')
        with open(commands_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        console.print(f"[bold red]Error loading commands:[/] {str(e)}")
        return None

def display_help():
    """Display formatted help information from commands.json."""
    commands = load_commands()
    if not commands:
        return
    
    for section, data in commands.items():
        # Create section header
        console.print(f"\n[bold]{data['emoji']} {data['title']}[/]")
        
        # Print commands and descriptions
        for cmd in data['commands']:
            console.print(f"[cyan]{cmd['syntax']}[/]")
            console.print(f"  [dim]# {cmd['description']}[/]")
        
        # Print examples
        console.print("\n[bold]Examples:[/]")
        for example in data['examples']:
            console.print(f"  [green]{example}[/]")
        
        console.print()  # Add blank line between sections

def format_response(response: str) -> None:
    """Format and print the response with syntax highlighting."""
    # Check if response contains code blocks
    if "```" in response:
        parts = response.split("```")
        for i, part in enumerate(parts):
            if i % 2 == 0:  # Regular text
                if part.strip():
                    console.print(Markdown(part))
            else:  # Code block
                # Extract language if specified
                if "\n" in part:
                    lang = part.split("\n")[0].strip()
                    code = "\n".join(part.split("\n")[1:])
                else:
                    lang = "text"
                    code = part
                
                syntax = Syntax(code, lang, theme="monokai", line_numbers=True)
                console.print(syntax)
    else:
        console.print(response)

def chat_with_assistant(message, context=None):
    """Send a message to the local AI assistant"""
    url = "http://localhost:8000/api/chat"
    
    data = {
        "message": message,
        "context": context or {}
    }
    
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()["response"]
    except requests.exceptions.RequestException as e:
        return f"Error communicating with assistant: {str(e)}"

def get_file_content(filepath):
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description="Chat with your AI Assistant")
    parser.add_argument("message", nargs="?", help="Message to send")
    parser.add_argument("--context", type=json.loads, help="JSON context data")
    
    args = parser.parse_args()
    
    # Create prompt session with history
    session = PromptSession(history=FileHistory('.chat_history'))
    
    if args.context and 'file' in args.context:
        args.context['content'] = get_file_content(args.context['file'])
    
    if not args.message:
        # Interactive mode
        console.print("[bold blue]Chat with your AI Assistant[/] (Ctrl+C to exit)")
        console.print("Type [bold green]/help[/] for available commands")
        
        while True:
            try:
                # Use prompt_toolkit for better input handling
                message = session.prompt("\nYou: ")
                
                if message.lower() in ['exit', 'quit']:
                    break
                elif message.lower() == '/help':
                    display_help()
                    continue
                
                response = chat_with_assistant(message, args.context)
                console.print("\n[bold cyan]Assistant:[/]")
                format_response(response)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[bold red]Error:[/] {str(e)}")
                break
    else:
        # Single message mode
        response = chat_with_assistant(args.message, args.context)
        format_response(response)

if __name__ == "__main__":
    main() 