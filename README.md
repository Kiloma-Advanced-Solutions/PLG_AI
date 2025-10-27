# MCP Chat Workshop

A multi-server chatbot application that integrates with Google Calendar using the Model Context Protocol (MCP). The chatbot can interact with users through natural language and perform actions like creating Google Calendar events, checking weather, and getting system information.

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Repository Structure](#repository-structure)
- [Google Calendar Setup](#google-calendar-setup)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Available Tools](#available-tools)

## 🚀 Features

- **Multi-Server MCP Architecture**: TypeScript and Python MCP servers working together
- **Google Calendar Integration**: Create and manage calendar events
- **Weather Information**: Get current weather for any city
- **File System Tools**: Check file information and system details
- **Mathematical Operations**: Calculate areas and perform calculations
- **Hebrew Language Support**: Full Hebrew interface and responses
- **Streaming Chat**: Real-time streaming responses from the chatbot

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                          │
│                 http://localhost:3000                       │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Chat API (FastAPI)                              │
│              http://localhost:8001                           │
│              chat_api.py                                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              MCP Service                                     │
│              mcp_service.py                                  │
│              Aggregates tools from multiple servers          │
└─────┬───────────────────────────────────────┬───────────────┘
      │                                       │
      ▼                                       ▼
┌─────────────────────┐           ┌─────────────────────┐
│ TypeScript MCP      │           │ Python MCP           │
│ Port: 8000          │           │ Port: 8002           │
│ ts_mcp_server.ts    │           │ python_mcp_server.py │
│ - time              │           │ - calculate_area     │
│ - get_weather       │           │ - get_file_info      │
│ - create_calendar   │           │ - get_system_info    │
└─────────────────────┘           └─────────────────────┘
                  ↓
         ┌─────────────────┐
         │ LLM Engine      │
         │ llm_engine.py   │
         │ OpenAI GPT-3.5  │
         └─────────────────┘
```

## 📁 Repository Structure

```
mcp_workshop/
├── Backend Core
│   ├── chat_api.py              # FastAPI chat endpoint (port 8001)
│   ├── mcp_service.py            # MCP integration service
│   ├── llm_engine.py             # OpenAI API engine
│   ├── config.py                 # Configuration management
│   └── models.py                 # Pydantic data models
│
├── MCP Servers
│   ├── ts_mcp_server.ts          # TypeScript MCP server (port 8000)
│   ├── python_mcp_server.py      # Python MCP server (port 8002)
│   └── dist/                     # Compiled TypeScript output
│       └── ts_mcp_server.js
│
├── Frontend
│   └── frontend/                  # React application
│       ├── src/App.js
│       └── build/
│
├── Configuration
│   ├── credentials.json           # Google OAuth credentials (gitignored)
│   ├── token.json                 # Google OAuth token (gitignored)
│   ├── package.json               # Node.js dependencies
│   ├── tsconfig.json              # TypeScript configuration
│   └── .env                       # Environment variables
│
└── Documentation
    └── README.md                  # This file
```

## 🔑 Files

### Backend Core Files

#### `chat_api.py`
- **Role**: FastAPI endpoint server
- **Port**: 8001
- **Responsibilities**:
  - Exposes `/chat` and `/chat/stream` endpoints
  - Integrates MCP service for tool execution
  - Falls back to direct LLM calls if MCP fails
  - Handles CORS for frontend

#### `mcp_service.py`
- **Role**: Multi-server MCP coordinator
- **Responsibilities**:
  - Connects to multiple MCP servers (TypeScript & Python)
  - Aggregates tools from all servers
  - Executes tools on their respective servers
  - Maps tool names to server URLs
  - Handles tool call routing

#### `llm_engine.py`
- **Role**: OpenAI API client
- **Responsibilities**:
  - Sends requests to OpenAI GPT-3.5-turbo
  - Handles streaming responses
  - Manages chat completion with tool calling
  - Provides structured completion support

#### `config.py`
- **Role**: Configuration management
- **Responsibilities**:
  - Loads environment variables
  - Defines MCP server URLs
  - Configures OpenAI API settings
  - Provides model parameters

#### `models.py`
- **Role**: Data models
- **Responsibilities**:
  - Defines Pydantic models for messages
  - Type-safe data structures

### MCP Servers

#### `ts_mcp_server.ts`
- **Role**: TypeScript MCP server
- **Port**: 8000
- **Tools Provided**:
  - `time` - Get current time in Israel
  - `get_weather` - Get weather for a city
  - `create_calendar_event` - Create Google Calendar events

#### `python_mcp_server.py`
- **Role**: Python MCP server
- **Port**: 8002
- **Tools Provided**:
  - `calculate_area` - Calculate area of shapes
  - `get_file_info` - Get file information
  - `get_system_info` - Get system information

### Configuration Files

#### `credentials.json`
- **Purpose**: Google OAuth client credentials
- **How to get**: Download from Google Cloud Console
- **Important**: This file is gitignored

#### `token.json`
- **Purpose**: OAuth access and refresh tokens
- **Generated**: Automatically during OAuth flow
- **Contains**: access_token, refresh_token, client_id, client_secret
- **Important**: This file is gitignored

## 🔐 Google Calendar Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Create Project" or select existing project
3. Give it a name (e.g., "mcp-workshop")

### Step 2: Enable Google Calendar API

1. Navigate to "APIs & Services" > "Library"
2. Search for "Google Calendar API"
3. Click "Enable"

### Step 3: Create OAuth Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Choose "Web Application" as application type
4. Configure OAuth consent screen (if prompted):
   - Choose "External" user type
   - Fill in app name, support email
   - Add scopes: `https://www.googleapis.com/auth/calendar`
   - Add test users (your email)
5. Download the JSON file and save as `credentials.json` in project root

### Step 4: Authenticate

The first time you run the TypeScript MCP server, it will use the `credentials.json` to authenticate. If you don't have a `token.json` yet, you'll need to run an OAuth flow.

**Option A - Automatic (if token expires):**
Run the TypeScript server, it will automatically authenticate if credentials are present.

**Option B - Manual Refresh:**
You may need to delete `token.json` and restart the server to trigger re-authentication.

### Step 5: Verify Access

Check `token.json` exists and contains:
- `token` (access token)
- `refresh_token` 
- `client_id` and `client_secret`
- `scopes` including calendar access

## 📦 Installation

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm

### Install Python Dependencies

```bash
pip install fastapi uvicorn openai python-dotenv mcp fastmcp googleapis
```

### Install Node.js Dependencies

```bash
npm install
```

### Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### Configure Environment

Create a `.env` file in the root directory:

```bash
OPENAI_API_KEY=your_openai_api_key_here
MCP_SERVERS=http://localhost:8000,http://localhost:8002
```

## 🚀 Running the Application

### Option 1: Quick Start (All Servers)

```bash
./start_servers.sh
```

This script will:
1. Start all 4 services in the background
2. Wait for each server to be ready
3. Print confirmation when all are up
4. Log output to `/tmp/*.log`

### Option 2: Manual Start (Separate Terminals)

**Terminal 1 - TypeScript MCP Server:**
```bash
npm run dev
```

**Terminal 2 - Python MCP Server:**
```bash
python3 python_mcp_server.py
```

**Terminal 3 - Chat API:**
```bash
python3 -m uvicorn chat_api:app --reload --port 8001
```

**Terminal 4 - Frontend:**
```bash
cd frontend && npm start
```

### View Logs

```bash
# View all logs
tail -f /tmp/ts_mcp.log      # TypeScript MCP
tail -f /tmp/python_mcp.log  # Python MCP
tail -f /tmp/chat_api.log    # Chat API
tail -f /tmp/frontend.log    # Frontend
```

## 🛠️ Available Tools

### From TypeScript Server (Port 8000)

| Tool | Description | Parameters |
|------|-------------|------------|
| `time` | Get current time in Israel | None |
| `get_weather` | Get weather for a city | `city` (string) |
| `create_calendar_event` | Create Google Calendar event | `summary`, `start_time`, `end_time`, `description` (optional) |

### From Python Server (Port 8002)

| Tool | Description | Parameters |
|------|-------------|------------|
| `calculate_area` | Calculate area of shapes | `shape` (string), `width` (float), `height` (float, optional) |
| `get_file_info` | Get file information | `file_path` (string) |
| `get_system_info` | Get system information | None |

## 🧪 Testing

### Test Chat API

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "מה השעה עכשיו?"}'
```

### Test MCP Servers

**TypeScript MCP:**
```bash
curl http://localhost:8000/health
```

**Python MCP:**
```bash
curl http://localhost:8002/health
```

## 🔒 Security Notes

- Never commit `credentials.json` or `token.json` to git
- Keep your OpenAI API key secure
- The `.gitignore` file should exclude sensitive files
- Use environment variables for production deployments

## 📚 Additional Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Google Calendar API](https://developers.google.com/calendar)

## 🐛 Troubleshooting

### "token.json not found"
- Run the OAuth authentication flow
- Check that `credentials.json` exists
- Delete `token.json` and restart to re-authenticate

### "No MCP tools available"
- Check that both MCP servers are running
- Verify server URLs in `config.py`
- Check server logs for errors

### "Google Calendar authentication failed"
- Verify `credentials.json` is valid
- Check `token.json` hasn't expired
- Re-run OAuth flow if needed

## 📝 License

MIT
