# MCP Chatbot with Google Calendar Integration

A chatbot application that uses the Model Context Protocol (MCP) to integrate Google Calendar functionality, allowing users to query and manage their calendar events through natural language.

## Features

- **Google Calendar Integration**: View, create, and search calendar events
- **MCP Tools**: Extensible tool system via MCP
- **Hebrew Language Support**: UI and responses in Hebrew
- **Modern Web Interface**: React-based chat interface
- **Multiple Tools**: Time, weather, file operations, math, and more

## Architecture

- **Frontend**: React application on port 3000
- **Chat API**: FastAPI server on port 8001
- **MCP Server**: FastMCP server on port 8000
- **Google Calendar API**: OAuth2 authenticated access

## Setup

### Prerequisites

```bash
# Python dependencies
pip install fastapi uvicorn openai python-dotenv mcp google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

# Node.js dependencies (for frontend)
cd frontend
npm install
```

### Google Calendar Setup

1. **Create Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one

2. **Enable Google Calendar API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click "Enable"

3. **Create OAuth Credentials**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Web Application" as application type
   - Download the JSON file

4. **Configure Credentials**:
   - Save the downloaded file as `credentials.json` in the project root
   - The file should look like:
     ```json
     {
       "installed": {
         "client_id": "...",
         "project_id": "...",
         "auth_uri": "https://accounts.google.com/o/oauth2/auth",
         "token_uri": "https://oauth2.googleapis.com/token",
         "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
         "client_secret": "...",
         "redirect_uris": ["http://localhost"]
       }
     }
     ```

5. **Initial Authentication**:
   ```bash
   python3 google_calendar_mcp.py
   ```
   - First run will open a browser for OAuth authentication
   - Grant Calendar permissions
   - A `token.json` file will be created automatically

### Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

## Running the Application

### 1. Start the MCP Server

```bash
python3 mcp_server.py
```

The server will start on `http://localhost:8000/mcp`

### 2. Start the Chat API

```bash
python3 chat_api.py
```

The API will start on `http://localhost:8001`

### 3. Start the Frontend

```bash
cd frontend
npm start
```

The frontend will start on `http://localhost:3000`

## Available Google Calendar Tools

### View Upcoming Events
**Hebrew**: "מה יש לי במערכת היום?" or "איזה פגישות יש לי?"  
**Tool**: `get_calendar_events(max_results=10)`

### View Past Events
**Hebrew**: "מה הפגישות האחרונות שהיו לי?" or "איזה אירועים קודמים?"  
**Tool**: `get_past_calendar_events(max_results=10)`

### View All Recent Events
**Hebrew**: "מה כל הפגישות שהופיעו ביומן שלי?" or "הראה לי את כל האירועים לאחרונה"  
**Tool**: `get_all_calendar_events(max_results=20, past_days=90)`

### Search Events
**Hebrew**: "חפש לי פגישות על פרויקט"  
**Tool**: `search_calendar_events(query="project", max_results=5)`

### Create New Event
**Hebrew**: "צור לי אירוע בשם פגישת צוות מחר בשעה 14:00"  
**Tool**: `create_calendar_event(summary, start_time, end_time, description)`

Example format:
- Start time: `2025-01-15T14:00:00`
- End time: `2025-01-15T15:00:00`

## Other Available Tools

- **Time**: `time()` - Get current time in Israel
- **Math**: `add()`, `multiply()`
- **Weather**: `get_weather(city)` - Get weather for any city
- **Files**: `read_file()`, `create_file()` - File operations
- **Cat Messages**: `get_cat_message()` - Fun cat images with messages

## Troubleshooting

### Google Calendar Connection Issues

1. **Token Expired**: Delete `token.json` and run `python3 google_calendar_mcp.py` again
2. **No Events Found**: Check that you granted Calendar permissions in OAuth
3. **Credentials Error**: Verify `credentials.json` is in the project root

### MCP Connection Issues

1. **404 Errors**: Ensure the URL is `http://localhost:8000/mcp` (with `/mcp` path)
2. **Session Terminated**: Restart the MCP server and chat API
3. **Tools Not Available**: Check that both servers are running

### Server Startup Issues

```bash
# Check if servers are running
ps aux | grep -E "mcp_server|chat_api"

# Kill existing processes
pkill -f "mcp_server.py"
pkill -f "chat_api.py"

# Restart servers
python3 mcp_server.py &  # Start in background
python3 chat_api.py &    # Start in background
```

## Project Structure

```
mcp_workshop/
├── README.md                 # This file
├── credentials.json          # Google OAuth credentials (not in git)
├── token.json                # OAuth token (not in git)
├── .env                      # Environment variables (not in git)
├── mcp_server.py             # MCP server with all tools
├── chat_api.py              # FastAPI chat backend
├── mcp_client.py             # MCP client implementation
├── google_calendar_mcp.py   # Google Calendar authentication
└── frontend/                 # React frontend
    ├── src/
    │   ├── App.js
    │   ├── App.css
    │   └── index.js
    └── package.json
```

## API Endpoints

- `POST /chat` - Send message to chatbot
- `GET /health` - Health check

## Development

### Adding New Tools

Add new tools to `mcp_server.py`:

```python
@mcp.tool()
def my_new_tool(param: str) -> str:
    """Tool description for the LLM."""
    return f"Result: {param}"
```

### Testing Google Calendar Connection

```bash
python3 google_calendar_mcp.py
```

Should print upcoming events if connection is working.

## License

MIT

## Author

Created for the MCP Workshop
