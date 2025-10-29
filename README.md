# MCP Workshop

A hands-on workshop for learning the Model Context Protocol (MCP) by building TypeScript MCP servers with a complete chat interface.

## 📚 Workshop Overview

This workshop teaches you how to build MCP (Model Context Protocol) servers in TypeScript. You'll learn to create tools that can be used by LLMs to extend their capabilities, and test them through a web-based chat interface.

## 🎯 Learning Objectives

- Understand the Model Context Protocol (MCP)
- Build TypeScript MCP servers using the official SDK
- Create and register MCP tools
- Handle HTTP transport for MCP servers
- Integrate external APIs (weather, flights) with MCP
- Test tools through a chat interface

## 📁 Repository Structure

```
mcp_workshop/
├── mcp_server_workshop.ts          # Workshop file - complete the exercises!
├── Solution/
│   └── SOL_mcp_server_workshop.ts  # Complete solution
├── python_mcp_server.py            # Python MCP server (reference)
├── chat_api.py                     # FastAPI backend for chat UI
├── mcp_service.py                  # MCP integration service
├── llm_engine.py                   # OpenAI integration (models & config)
├── frontend/                        # React chat interface
│   ├── src/App.js
│   └── package.json
├── package.json                     # Node.js dependencies
├── tsconfig.json                    # TypeScript configuration
├── requirements.txt                 # Python dependencies
├── start.sh                         # Start all services script
├── .env                             # Environment variables (create this)
└── README.md                        # This file
```

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- Python 3.8+
- npm or yarn

### Installation

```bash
# Install Node.js dependencies
npm install

# Install frontend dependencies
cd frontend && npm install && cd ..

# (Optional) Create Python virtual environment and install dependencies
python3 -m venv myenv
source myenv/bin/activate  # On Windows: myenv\Scripts\activate
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file in the root directory:

```bash
# Required for flight search tool (Exercise 3)
SERPAPI_API_KEY=your_serpapi_key_here

# Required for chat interface
OPENAI_API_KEY=your_openai_key_here
MCP_SERVERS=http://localhost:8000,http://localhost:8002
```

Get your API keys:
- SerpAPI: https://serpapi.com/manage-api-key
- OpenAI: https://platform.openai.com/api-keys

### Start Everything

```bash
# Make script executable (first time only)
chmod +x start.sh

# Start all services (workshop mode)
./start.sh

# Or start with solution
./start.sh solution
```

This will:
1. Start TypeScript MCP Server (port 8000)
2. Start Python MCP Server (port 8002)
3. Start Chat API (port 8001)
4. Start Frontend UI (port 3000)
5. Open your browser to http://localhost:3000

## 📝 Exercises

### Exercise 1: Time Tool ⏳

**Location**: `mcp_server_workshop.ts` - Look for `Ex-1: Time Tool`

**Task**: Complete the `time` tool to return the current time in Israel (Asia/Jerusalem timezone).

**Hint**: Use JavaScript's `Date` object with `toLocaleString()` method.

### Exercise 2: Weather Tool 🌦️

**Location**: `mcp_server_workshop.ts` - Look for `Ex-2: Weather Tool`

**Task**: Implement the weather tool using the `https` library to fetch weather data from `wttr.in`.

### Important Notes

**Hint**: 
- Use `https.get()` to fetch data
- Parse JSON response
- Extract weather data from `current_condition[0]`

### Exercise 3: Flight Search Tool ✈️

**Location**: `mcp_server_workshop.ts` - Look for `Ex-3: Flight Search Tool`

**Task**: Implement flight search using SerpAPI to call the Google Flights API.

**"Error searching flights"**
- Check server logs: `tail -f /tmp/python_mcp.log`
- Verify the virtual environment is activated
- Restart the Python MCP server

**Hint**:
- Check for API key first
- Use `getJson()` function (callback-based)
- Set `type: 1` for round trip when `return_date` is provided, `type: 2` for one-way
- Wrap `getJson` in a Promise to use async/await

**API Reference**: https://serpapi.com/google-flights-api

## 🛠️ Running the Workshop

Start all services including the chat UI:

```bash
./start.sh
```

This starts everything and opens the browser to the chat interface.



## 🌐 Services

The workshop includes a complete testing environment:

- **TypeScript MCP Server** (port 8000) - Your workshop exercises
- **Python MCP Server** (port 8002) - Additional reference tools
- **Chat API** (port 8001) - FastAPI backend that aggregates MCP tools
- **Frontend UI** (port 3000) - React chat interface for testing

## 📚 Resources

### MCP Documentation
- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)
- [MCP Specification](https://modelcontextprotocol.io/)
- [MCP Tutorial](https://github.com/modelcontextprotocol/typescript-sdk/tree/main/examples)

### APIs Used
- **Weather**: [wttr.in API](https://wttr.in/:help)
- **Flights**: [SerpAPI Google Flights](https://serpapi.com/google-flights-api)

## 🐛 Troubleshooting

### "Cannot find module 'serpapi'"
```bash
npm install serpapi
```

### "SERPAPI_API_KEY not set"
- Create a `.env` file
- Add: `SERPAPI_API_KEY=your_key_here`
- Restart the server

### Port already in use
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill    # TypeScript MCP
lsof -ti:8001 | xargs kill    # Chat API
lsof -ti:8002 | xargs kill    # Python MCP
lsof -ti:3000 | xargs kill    # Frontend
```

### Frontend won't start
```bash
# Install frontend dependencies
cd frontend && npm install && cd ..
```

### Python dependencies missing
```bash
# Create virtual environment
python3 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
```

### TypeScript compilation errors
```bash
# Check the error message
npm run build

# Common issues:
# - Missing imports
# - Syntax errors (check semicolons, brackets)
# - Type mismatches
```

## 📝 Solution

If you get stuck, check `Solution/SOL_mcp_server_workshop.ts` for complete implementations. But try to solve the exercises first!

## 🎓 Workshop Tips

1. **Read the TODOs**: Each exercise has clear TODO comments with hints
2. **Check the examples**: The `power_calculator` tool shows the pattern
3. **Test through the UI**: Use the chat interface at http://localhost:3000 to test your tools
4. **Test incrementally**: Test each tool after implementing it
5. **Use TypeScript**: The type system will help catch errors
6. **Read error messages**: They usually point to the problem

