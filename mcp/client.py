import os
import json
import dotenv

from mcp import ClientSession, types
from mcp.client.streamable_http import streamablehttp_client

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

# Load environment variables
dotenv.load_dotenv()

# HTTP server URL
server_url = "http://localhost:8000/mcp"

def call_llm(prompt, functions):
    token = os.environ["GITHUB_TOKEN"]
    endpoint = "https://models.inference.ai.azure.com"
    model_name = "gpt-4o"

    client = ChatCompletionsClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(token),
    )

    print("\nCalling LLM...")
    response = client.complete(
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        model=model_name,
        tools=functions,  # Optional
        temperature=1.0,
        max_tokens=1000,
        top_p=1.0,
    )

    response_message = response.choices[0].message
    print("\nResponse:\n", response_message)

    functions_to_call = []

    if response_message.tool_calls:
        for tool_call in response_message.tool_calls:
            print("TOOL:", tool_call)
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            functions_to_call.append({"name": name, "args": args})

    return functions_to_call


def convert_to_llm_tool(tool):
    tool_schema = {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "type": "function",
            "parameters": {
                "type": "object",
                "properties": tool.inputSchema["properties"]
            }
        }
    }
    return tool_schema


async def run():
    async with streamablehttp_client(server_url) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # List available resources
            resources = await session.list_resources()
            print("\nAvailable Resources:")
            for resource in resources:
                print("- Resource:", resource)

            # List available tools
            tools = await session.list_tools()
            print("\nAvailable Tools:")
            functions = []
            for tool in tools.tools:
                print("- Tool:", tool.name, tool.inputSchema["properties"])
                functions.append(convert_to_llm_tool(tool))

            # LLM prompt
            # prompt = "I have 4 bills of 20$ and another 10$. How much money do I have?"
            prompt = "What time is it?"

            # Ask LLM what tools to call, if any
            functions_to_call = call_llm(prompt, functions)
            print("\n Functions to call:", functions_to_call)

            # Call suggested functions
            for f in functions_to_call:
                result = await session.call_tool(f["name"], arguments=f["args"])
                print("\n Tools result:", result.content)


if __name__ == "__main__":
    import asyncio
    asyncio.run(run())
