import json
import os
from typing import Dict, Any

def load_commands() -> Dict[str, Any]:
    """Load and return commands from commands.json."""
    try:
        commands_path = os.path.join('app', 'config', 'commands.json')
        with open(commands_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading commands: {e}")
        return {}

def format_command_help(commands: Dict[str, Any]) -> str:
    """Format commands into a readable help string."""
    help_text = []
    
    for section, data in commands.items():
        # Add section header
        help_text.append(f"\n{data['emoji']} {data['title']}\n")
        
        # Add commands with descriptions
        for cmd in data['commands']:
            help_text.append(f"{cmd['syntax']}")
            help_text.append(f"    # {cmd['description']}")
        
        # Add examples
        help_text.append("\nExamples:")
        for example in data['examples']:
            help_text.append(f"    {example}")
        
        help_text.append("")  # Add blank line between sections
    
    return "\n".join(help_text)

def show_help() -> str:
    """Display help information about available commands."""
    commands = load_commands()
    if not commands:
        return "Error: Could not load command help information."
    
    return format_command_help(commands)

# Example usage in your cursor chat handler:
def handle_help_command():
    """Handle the /help command."""
    return show_help() 