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

## Configuration Setup

Before running the application, you need to set up your configuration files. Example files are provided for all sensitive configurations:

### 1. Google OAuth Credentials

Copy `app/config/credentials.example.json` to `app/config/credentials.json` and fill in your Google OAuth credentials:

```json
{
  "installed": {
    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "client_secret": "YOUR_CLIENT_SECRET",
    "redirect_uris": ["http://localhost"]
  }
}
```

### 2. Calendar Configuration

Copy `app/config/calendar_config.example.json` to `app/config/calendar_config.json` and update with your calendar settings:

```json
{
  "calendars": {
    "personal": "your.personal@gmail.com",
    "work": "your.work@company.com"
  },
  "settings": {
    "timezone": "America/Edmonton"
  }
}
```

### 3. Frontend Secrets

Copy `dashboard-chat/src/config/secrets.example.ts` to `dashboard-chat/src/config/secrets.ts` and update with your configuration:

```typescript
export const CALENDAR_NAMES = {
  PERSONAL: "your.personal@gmail.com",
  WORK: "your.work@company.com",
  // ... other calendars
};

// Calendar colors for visual distinction
export const CALENDAR_COLORS = {
  [CALENDAR_NAMES.PERSONAL]: "#007bff", // Blue
  [CALENDAR_NAMES.WORK]: "#28a745", // Green
  // ... other calendar colors
};

// Configure which calendars are visible by default
export const CALENDAR_VISIBILITY = {
  [CALENDAR_NAMES.PERSONAL]: true, // Show by default
  [CALENDAR_NAMES.WORK]: false, // Hidden by default
  // ... other calendar visibility settings
};

export const GOOGLE_MAPS_API_KEY = "YOUR_GOOGLE_MAPS_API_KEY";
```

### 4. Environment Variables

Copy `.env.example` to `.env` and update with your API keys:

```bash
VITE_GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
```

Note: All example files are tracked in git, but the actual configuration files are gitignored. Never commit sensitive credentials to version control.

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
