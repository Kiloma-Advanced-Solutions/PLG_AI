import os
from agents import Agent, Runner, OpenAIChatCompletionsModel, AsyncOpenAI
from agents.model_settings import ModelSettings
from agents.mcp import MCPServerStreamableHttp
from core.config import llm_config
from core.llm_engine import llm_engine
from core.models import TriageAgentResponse

# Get API key from environment variable, or use a placeholder for custom servers
api_key = os.getenv("OPENAI_API_KEY", "dummy-key")

# Initialize MCP servers with Streamable HTTP transport
# Set longer timeouts to prevent session closure during agent execution
mcp_internet = MCPServerStreamableHttp(
    params={
        "url": "http://localhost:8000/mcp",
        "timeout": 300.0,  # 5 minutes
        "sse_read_timeout": 300.0,  # 5 minutes
    },
    cache_tools_list=False  # Don't cache to avoid stale sessions
)
mcp_io = MCPServerStreamableHttp(
    params={
        "url": "http://localhost:8001/mcp",
        "timeout": 300.0,  # 5 minutes
        "sse_read_timeout": 300.0,  # 5 minutes
    },
    cache_tools_list=False  # Don't cache to avoid stale sessions
)

model = OpenAIChatCompletionsModel( 
    model="gaunernst/gemma-3-12b-it-qat-autoawq",
    openai_client=AsyncOpenAI(
        base_url=f"{llm_config.vllm_url}/v1",
        api_key=api_key
    )
)


triage_agent = Agent(name="Triage Agent",
              instructions="""You are a triage assistant that determines whether user queries need specialized agents.

Available specialized agents:
- "IO": For file system operations, reading/writing files
- "Internet": For web searches, fetching external data

CRITICAL: You MUST respond with ONLY valid JSON. No explanations, no markdown, no code blocks.

JSON format (required):
{
  "should_handoff": true/false,
  "handoff_agent": "IO" or "Internet" (only if should_handoff is true, otherwise "null"),
  "handoff_reason": "brief explanation"
}

Respond with JSON only.""",
              model=model,
              )


io_agent = Agent(
    name="IO Agent",
    instructions="You are a helpful assistant for IO operations. Use the available tools to help users with file operations.",
    model=model,
    mcp_servers=[mcp_io],
    model_settings=ModelSettings(tool_choice="required"),
)

internet_agent = Agent(
    name="Internet Agent",
    instructions="You are a helpful assistant for Internet operations. Use the available tools to help users with weather, time, and other internet-based queries. Return the tool result directly to the user.",
    model=model,
    mcp_servers=[mcp_internet],
    model_settings=ModelSettings(
        tool_choice="required",
        parallel_tool_calls=False  # Disable parallel calls to simplify
    ),
)

general_agent = Agent(name="General Agent",
              instructions="You are a helpful assistant for queries that don't require specialized help.",
              model=model,
              )
