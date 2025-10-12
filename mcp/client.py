import os
import json
import dotenv
import httpx

from mcp import ClientSession, types
from mcp.client.streamable_http import streamablehttp_client

# Load environment variables
dotenv.load_dotenv()

# HTTP server URLs
mcp_server_url = "http://localhost:8000/mcp"  # For tools providing and execution
vllm_url = "http://localhost:8060/v1/chat/completions"  # The LLM API

async def call_llm(prompt, functions):
    """Call vLLM with LLM API"""
    print("\nCalling LLM...")
    
    # Prepare messages in OpenAI format
    system_content = "You are a helpful assistant."
    
    # Add available tools information to the system message
    if functions:
        system_content += "\n\nYou have access to the following tools:\n"
        for func in functions:
            func_info = func["function"]
            system_content += f"\n- {func_info['name']}: {func_info['description']}\n"
            props = func_info['parameters']['properties']
            if props:
                system_content += f"  Parameters:\n"
                for param_name, param_info in props.items():
                    param_type = param_info.get('type', 'any')
                    param_desc = param_info.get('description', '')
                    system_content += f"    - {param_name} ({param_type}): {param_desc}\n"
        
        system_content += "\n\nWhen you need to use a tool, respond ONLY with a JSON object in this exact format:"
        system_content += '\n{"tool": "tool_name", "arguments": {"param1": value1, "param2": value2}}'
        system_content += "\n\nDo not include any other text in your response when calling a tool."
    
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": prompt},
    ]
    
    # Make request directly to vLLM (bypassing LLM API)
    payload = {
        "model": "gaunernst/gemma-3-12b-it-qat-autoawq",
        "messages": messages,
        "stream": True,  # Use streaming
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Stream the response
            full_response = ""
            async with client.stream("POST", vllm_url, json=payload) as response:
                if response.status_code != 200:
                    print(f"Error calling vLLM: {response.status_code}")
                    error_text = await response.aread()
                    print(f"Response: {error_text.decode()}")
                    return []
                
                # Collect all chunks
                async for line in response.aiter_lines():
                    if line.startswith('data: '):
                        data = line.replace('data: ', '').strip()
                        if data and data != '[DONE]':
                            try:
                                chunk = json.loads(data)
                                if 'choices' in chunk and len(chunk['choices']) > 0:
                                    delta = chunk['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    if content:
                                        full_response += content
                            except json.JSONDecodeError:
                                pass
            
            print("\nLLM Response:")
            print(full_response)
            
            # Parse the response to extract tool calls
            functions_to_call = []
            
            # Try to parse the response as JSON (tool call)
            try:
                # Clean the response
                response_clean = full_response.strip()
                
                # Try to find JSON in the response
                if '{' in response_clean and '}' in response_clean:
                    # Extract JSON from the response
                    start_idx = response_clean.find('{')
                    end_idx = response_clean.rfind('}') + 1
                    json_str = response_clean[start_idx:end_idx]
                    
                    tool_call = json.loads(json_str)
                    if 'tool' in tool_call:
                        # Handle missing arguments field (default to empty dict)
                        args = tool_call.get('arguments', {})
                        functions_to_call.append({
                            "name": tool_call['tool'],
                            "args": args
                        })
                        print(f"\nExtracted tool call: {tool_call['tool']} with args {args}")
            except json.JSONDecodeError as e:
                print(f"Could not parse response as tool call JSON: {e}")
            except Exception as e:
                print(f"Error parsing response: {e}")
            
            return functions_to_call
            
    except Exception as e:
        print(f"Error calling vLLM: {e}")
        import traceback
        traceback.print_exc()
        return []


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
    async with streamablehttp_client(mcp_server_url, auth=None) as (read, write, get_session_id):
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
            functions_to_call = await call_llm(prompt, functions)
            print("\n Functions to call:", functions_to_call)

            # Call suggested functions
            for f in functions_to_call:
                result = await session.call_tool(f["name"], arguments=f["args"])
                print("\n Tools result:", result.content)


if __name__ == "__main__":
    import asyncio
    asyncio.run(run())
