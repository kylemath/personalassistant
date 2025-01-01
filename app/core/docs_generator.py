import json
import os

class DocsGenerator:
    def __init__(self):
        self.commands = self._load_commands()
    
    def _load_commands(self):
        """Load commands from JSON file."""
        commands_path = os.path.join('app', 'config', 'commands.json')
        with open(commands_path, 'r') as f:
            return json.load(f)
    
    def generate_html(self):
        """Generate HTML for command reference."""
        html = ['<div id="command-reference"><h2>Available Commands</h2>']
        
        for section, data in self.commands.items():
            html.append(f'''
                <div class="command-section">
                    <h2>{data['emoji']} {data['title']}</h2>
                    {''.join(f'<div class="command">{cmd["syntax"]} <span class="description"># {cmd["description"]}</span></div>' for cmd in data['commands'])}
                    <div class="examples">
                        Examples:<br>
                        {'<br>'.join(f'<code>{example}</code>' for example in data['examples'])}
                    </div>
                </div>
            ''')
        
        html.append('</div>')
        return '\n'.join(html)
    
    def generate_markdown(self):
        """Generate markdown for README."""
        md = ['## Available Commands\n']
        
        for section, data in self.commands.items():
            md.append(f"### {data['title']}\n```")
            for cmd in data['commands']:
                md.append(f"{cmd['syntax']}    # {cmd['description']}")
            md.append('\n'.join(['', 'Examples:', *data['examples'], '```', '']))
        
        return '\n'.join(md)

    def update_files(self):
        """Update HTML file only."""
        try:
            # Update HTML
            html_template_path = os.path.join('app', 'static', 'index.html')
            with open(html_template_path, 'r') as f:
                html_content = f.read()
            
            # Get base template without command reference sections
            base_template = html_content.split('<!-- Command Reference Section -->')[0]
            
            # Add our new content
            new_html = base_template + '<!-- Command Reference Section -->' + self.generate_html()
            
            with open(html_template_path, 'w') as f:
                f.write(new_html)
                
            print("Documentation updated successfully!")
            
        except Exception as e:
            print(f"Error updating documentation: {e}") 