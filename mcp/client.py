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
        
        system_content += "\n\nRESPONSE FORMAT:"
        system_content += '\n- Call ONE tool at a time: {"tool": "name", "arguments": {...}}'
        system_content += '\n- When you have the FINAL ANSWER (no more calculations needed): []'
        system_content += "\n\nReturn ONLY JSON - either the tool call or []."
    
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
            
            try:
                # Clean and parse response
                response_clean = full_response.strip().replace('```json', '').replace('```', '').strip()
                parsed = json.loads(response_clean)
                
                # Normalize to list (handle both single object and array)
                tool_calls = parsed if isinstance(parsed, list) else [parsed] if parsed else []
                
                # Extract tool calls
                for tool_call in tool_calls:
                    if isinstance(tool_call, dict) and 'tool' in tool_call:
                        args = tool_call.get('arguments', {})
                        functions_to_call.append({"name": tool_call['tool'], "args": args})
                        
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                print(f"Could not parse tool calls: {e}")
            
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
            prompt = "I have 3 bills of 50$ and another 20$ and another 40$. How much money do I have?"
            # prompt = "What time is it?"

            # Agentic loop: LLM sees intermediate results and decides next steps
            max_iterations = 5
            iteration = 0
            done = False;
            work_log = []
            
            while not done and iteration < max_iterations:
                print(f"\n--- Iteration {iteration + 1} ---")
                
                # Build conversation with all previous work
                if work_log:
                    history = f"Question: {prompt}\n\nCalculations completed:\n"
                    for step in work_log:
                        history += f"- {step['tool']}({step['args']}) = {step['result']}\n"
                    history += f"\nCurrent answer: {work_log[-1]['result']}"
                    history += "\n\nIf this answers the question, return []. Otherwise, call the next tool:"
                else:
                    history = prompt

                print(f"========history:========\n{history}\n================")

                # Ask LLM what tools to call
                functions_to_call = await call_llm(history, functions)
                
                if not functions_to_call:
                    print("✓ Done! Final answer:", work_log[-1]['result'] if work_log else "No calculation needed")
                    break
                
                # Execute first tool only
                tool = functions_to_call[0]
                
                if not done:
                    result = await session.call_tool(tool["name"], arguments=tool["args"])
                    tool_result = result.content[0].text if result.content else "No result"
                    print(f"Result: {tool_result}")
                    
                    # Log this step
                    work_log.append({"tool": tool['name'], "args": tool['args'], "result": tool_result})
                
                iteration += 1


if __name__ == "__main__":
    import asyncio
    asyncio.run(run())
