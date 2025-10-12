# MCP Client with Local LLM

This MCP (Model Context Protocol) client demonstrates how to connect an MCP server with tools to the local LLM API for intelligent tool calling.

## Architecture

```
┌─────────────┐      ┌─────────────┐      
│  MCP Client │ ───▶ │  MCP Server │      
│  (client.py)│      │  (server.py)│      
│             │      │  port 8000  │      
│             │      └─────────────┘      
│             │                           
│             │      ┌──────────────┐     
│             │ ───▶ │   vLLM       │     
└─────────────┘      │  (port 8060) │     
                     └──────────────┘     
```

**Note**: The client calls vLLM directly (port 8060) to avoid the Hebrew chat system prompt in the LLM API (port 8090).

## Setup

1. **Install dependencies** (if you haven't already):
   ```bash
   cd mcp
   pip install -r requirements.txt
   ```

2. **Start the vLLM server** (if not already running):
   ```bash
   # The vLLM should be running on port 8060
   # The client calls vLLM directly, no need for the LLM API
   ```

3. **Start the MCP Server** (in a separate terminal):
   ```bash
   cd mcp
   python server.py
   ```

4. **Run the MCP Client**:
   ```bash
   cd mcp
   python client.py
   ```

## How It Works

1. **MCP Server** (`server.py`):
   - Exposes tools like `add()`, `multiply()`, and `time()`
   - Runs on port 8000

2. **MCP Client** (`client.py`):
   - Connects to the MCP server to discover available tools
   - Sends prompts directly to vLLM
   - Parses the LLM's response to identify tool calls
   - Executes the tools via the MCP server
   - Returns the results

3. **vLLM** (port 8060):
   - Runs your local Gemma-3 12B model
   - Provides OpenAI-compatible chat completions endpoint
   - Called directly by the MCP client

## Key Features

- **Direct vLLM Integration**: Connects directly to vLLM on port 8060 (bypasses LLM API)
- **Streaming Support**: Handles streaming responses from vLLM
- **Tool Discovery**: Automatically discovers available tools from the MCP server
- **Authentication Bypass**: Configured for local development without authentication (`auth=None`)
- **Flexible Tool Call Parsing**: Handles both `{"tool": "name", "arguments": {...}}` and `{"tool": "name"}` formats

## Testing

The client includes a test prompt: "What time is it?"

This should:
1. Connect to the MCP server
2. Discover the `time()` tool
3. Send the prompt to your local LLM
4. Parse the LLM's response to extract the tool call
5. Call the `time()` tool
6. Display the result


## Configuration

The client uses these default URLs:
- **MCP Server**: `http://localhost:8000/mcp`
- **vLLM**: `http://localhost:8060/v1/chat/completions`

We can modify these in `client.py` if the services run on different ports.

