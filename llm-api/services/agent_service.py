from typing import Any


import os
from agents import Agent, Runner, set_tracing_disabled
from agents.mcp import MCPServerStreamableHttp
from agents.model_settings import ModelSettings
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from openai import AsyncOpenAI
from core.config import llm_config

# Disable tracing FIRST, before any agents are created
# This must be called at module import time to prevent tracing from being enabled
set_tracing_disabled(True)

# === MODEL SETUP ===
api_key = os.getenv("OPENAI_API_KEY", "dummy-key")
# Ensure OPENAI_API_KEY is set in environment for agents framework
if "OPENAI_API_KEY" not in os.environ:
    os.environ["OPENAI_API_KEY"] = api_key

model = OpenAIChatCompletionsModel(
    model="gaunernst/gemma-3-12b-it-qat-autoawq",
    openai_client=AsyncOpenAI(
        base_url=f"{llm_config.vllm_url}/v1",
        api_key=api_key,
    ),
)


# === MCP SERVERS (Streamable HTTP) ===
# Create MCP server instances at module level
# They will be connected on-demand by chat_service.py
mcp_internet = MCPServerStreamableHttp(
    name="Internet MCP Server",
    params={
        "url": "http://localhost:8000/mcp",
        "timeout": 300.0,
        "sse_read_timeout": 300.0,
    },
    cache_tools_list=False,
)

mcp_io = MCPServerStreamableHttp(
    name="IO MCP Server",
    params={
        "url": "http://localhost:8001/mcp",
        "timeout": 300.0,
        "sse_read_timeout": 300.0,
    },
    cache_tools_list=False,
)


io_agent = Agent(
    name="IO Agent",
    instructions=(
        "You are a helpful assistant for IO operations. "
        "You MUST use the function calling API to call tools - do NOT write tool calls as text. "
        "Use the available tools to perform file system tasks. "
        "After receiving a tool result, return ONLY the result value to the user - do not add explanations or format it as a function call."
    ),
    model=model,
    mcp_servers=[mcp_io],
    model_settings=ModelSettings(
        tool_choice="required",
        max_tokens=200,  # Reduced to force concise responses
    ),
)

internet_agent = Agent(
    name="Internet Agent",
    instructions=(
        "You are a helpful assistant for Internet operations. "
        "You MUST use the function calling API to call tools - do NOT write tool calls as text. "
        "When the user asks about weather, call the get_weather tool with the city name. "
        "When the user asks about time, call the time tool. "
        "After receiving a tool result, return ONLY the result value to the user - do not add explanations or format it as a function call."
    ),
    model=model,
    mcp_servers=[mcp_internet],
    model_settings=ModelSettings(
        tool_choice="required",
        parallel_tool_calls=False,
        max_tokens=200,  # Reduced to force concise responses
    ),
)


triage_agent = Agent[Any](
    name="Triage agent",
    instructions=(
        "You are a routing assistant. Your ONLY job is to call the appropriate transfer function.\n\n"
        "For questions about time, weather, or web searches -> call transfer_to_internet_agent\n"
        "For file operations -> call transfer_to_io_agent\n\n"
        "You must always call one of the transfer functions. Never respond with text."
    ),
    model=model,
    handoffs=[io_agent, internet_agent],
    model_settings=ModelSettings(
        tool_choice="required",
        max_tokens=100,  # Limit response length
    )
)
