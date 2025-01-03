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
   source venv/bin/activate  # On Unix/macOS
   # or
   .\venv\Scripts\activate  # On Windows
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

1. **Start Ollama**

   ```bash
   ollama serve
   ```

2. **Start the backend server**

   ```bash
   source venv/bin/activate
   # For local access only:
   uvicorn app.main:app --reload
   # For network access:
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Start the frontend server**
   ```bash
   cd dashboard-chat
   npm install
   npm run dev
   ```

The application will be available at:

- Local access: `http://localhost:5173`
- Network access: `http://<your-ip>:5173`

Use the help button (?) or press 'h' to see available commands.

## Network Access

To access the application from other devices on your local network:

1. Find your computer's IP address:

   ```bash
   # On macOS/Linux
   ifconfig | grep "inet "
   # On Windows
   ipconfig
   ```

2. On other devices, access the application at:
   - Frontend: `http://<your-ip>:5173`
   - Backend API: `http://<your-ip>:8000`

Note: Make sure your firewall settings allow incoming connections on ports 5173 and 8000.
