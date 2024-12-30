# AI Assistant with Calendar, Email, and Todo Integration

A local AI assistant powered by Ollama that integrates with Google Calendar, Gmail, and includes a todo list manager.

## Prerequisites

1. **Python 3.8+**
2. **Ollama** installed on your system
3. **Google Cloud Platform account** for API access

## Installation

1. **Install Ollama**

   ```bash

   brew install ollama
   ```

2. **Start Ollama and pull model**

   ```bash
   # Start Ollama server
   ollama serve

   # In a new terminal, pull the model
   ollama pull mistral:7b-instruct
   ```

3. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/ai-assistant.git
   cd ai-assistant
   ```

4. **Create and activate a virtual environment**

   ```bash
   python -m venv venv

   ```

5. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

6. **Set up Google Cloud credentials**
   - Go to the [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project
   - Enable the Gmail API and Google Calendar API
   - Create OAuth 2.0 credentials
   - Download the credentials and save as `app/config/credentials.json`

## Configuration

1. **Create config directory**
   ```bash
   mkdir -p app/config
   ```

## Running the Application

2. **Start Ollama**

   ```bash
   ollama serve
   ```

3. **In a new terminal Start the web server**
   ```bash
   uvicorn app.main:app --reload
   ```

The application will be available at the indicated webaddress or `http://localhost:8000`

## Available Commands

### Calendar

```
/calendar list
/calendar add "Title" "Time" ["End Time"] ["Description"] ["Location"] [--recurring daily/weekly/monthly/yearly]

Examples:
/calendar add "Team Meeting" "tomorrow at 2pm"
/calendar add "Weekly Standup" "monday 9am" --recurring weekly
```

### Email

```
/email list [search query]
/email send "recipient@email.com" "Subject" "Body"
/email reply <email_id> "Reply message"

Examples:
/email list unread
/email send "john@example.com" "Meeting Notes" "Here are the notes..."
```

### Todo List

```
/todo add "Task" [--priority high/medium/low] [--category name] [--due "date"] ["notes"]
/todo list [category] [--priority high/medium/low]
/todo done <todo_id>
/todo delete <todo_id>

Examples:
/todo add "Write documentation" --priority high --category work --due "friday 5pm"
/todo list work --priority high
```

### Memory

```
/addfact [category:] <fact>
/listfacts [category]
/deletefact <fact_id>

Examples:
/addfact work: Meeting every Monday at 10am
/listfacts work
```

## First-Time Setup

1. **Start the server and open the web interface**
2. **Authenticate with Google**
   - The first calendar or email command will open your browser
   - Select your Google account
   - Grant the requested permissions
   - Authentication tokens will be saved locally

## File Structure

```
app/
├── config/
│   └── credentials.json
├── core/
│   ├── calendar_manager.py
│   ├── gmail_manager.py
│   ├── llm.py
│   ├── memory.py
│   └── todo_manager.py
├── static/
│   └── index.html
└── main.py
```

## Troubleshooting

1. **Authentication Issues**

   - Delete token files to force re-authentication:
     ```bash
     rm *_token.pickle
     ```

2. **Ollama Issues**

   - Ensure Ollama is running: `ollama serve`
   - Check model is installed: `ollama list`

3. **Permission Issues**
   - Check Google Cloud Console for enabled APIs
   - Verify OAuth consent screen configuration
   - Ensure credentials.json is in the correct location
