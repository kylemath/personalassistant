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
   source venv/bin/activate
   uvicorn app.main:app --reload
   ```

The application will be available at `http://localhost:8000`. Use the help button (?) or press 'h' to see available commands.

##
