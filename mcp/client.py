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


def create_system_prompt(functions=None, user_info=None):
    system_prompt = "You are a helpful assistant."
    
    # Add user info if available
    if user_info:
        system_prompt += f"\n\nThe user information is:\n{user_info}."
    
    # Add available tools information to the system prompt
    if functions:
        system_prompt += "\n\nYou have access to the following tools:\n"
        for func in functions:
            func_info = func["function"]
            system_prompt += f"\n- {func_info['name']}: {func_info['description']}\n"
            props = func_info['parameters']['properties']
            if props:
                system_prompt += f"  Arguments:\n"
                for param_name, param_info in props.items():
                    param_type = param_info.get('type', 'any')
                    param_desc = param_info.get('description', '')
                    system_prompt += f"    - {param_name} ({param_type}): {param_desc}\n"
        
        system_prompt += "\n\nRESPONSE FORMAT (return ONLY JSON, no explanations):"
        system_prompt += '\n- To call a tool: {"tool": "name", "arguments": {...}}'
        system_prompt += '\n- When finished: []'
        system_prompt += "\n\nIMPORTANT: Return ONLY the JSON - no text, no explanations."

    return system_prompt




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



async def stream_vllm_response(messages, max_tokens=1000):
    """Stream response from vLLM and collect full text"""
    payload = {
        "model": "gaunernst/gemma-3-12b-it-qat-autoawq",
        "messages": messages,
        "stream": True,
        "temperature": 0.7,
        "max_tokens": max_tokens
    }
    
    try:
        full_response = ""
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", vllm_url, json=payload) as response:
                if response.status_code != 200:
                    print(f"Error: {response.status_code}")
                    return ""
                
                async for line in response.aiter_lines():
                    if line.startswith('data: ') and '[DONE]' not in line:
                        try:
                            chunk = json.loads(line[6:])
                            content = chunk['choices'][0]['delta'].get('content', '')
                            full_response += content
                        except:
                            pass
        return full_response.strip()
    except Exception as e:
        print(f"Streaming error: {e}")
        return ""


async def get_final_answer(system_prompt, prompt):
    """Get final answer without tools"""
    
    messages = [
        {"role": "system", "content": system_prompt},   # System prompt with user info (no functions defenition)
        {"role": "user", "content": prompt}             # User question with all previous calculations (if existed)
    ]

    # print(f"=== {messages} ===")
    return await stream_vllm_response(messages, max_tokens=200)


async def call_llm(system_prompt, prompt):
    """Call vLLM with LLM API"""
    print("\nCalling LLM...")


    # Prepare messages in OpenAI format
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    
    print(f"\n{messages}\n")
    
    # Stream response from vLLM
    full_response = await stream_vllm_response(messages)
    
    if not full_response:
        return []
    
    print("\nLLM Response:")
    print(full_response)
    
    # Parse the response to extract tool calls
    try:
        # Clean response
        response_clean = full_response.replace('```json', '').replace('```', '').strip()
        
        # If [] in model response - Done, No more tool calls needed
        if '[]' in response_clean:
            return []
        
        # Extract JSON substring if present
        if "{" in response_clean and "}" in response_clean:
            json_str = response_clean[response_clean.find("{") : response_clean.rfind("}") + 1]
            parsed = json.loads(json_str)
            
            if 'tool' in parsed:
                args = parsed.get('arguments', {})
                return [{"name": parsed['tool'], "args": args}]
                
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        print(f"Could not parse response: {e}")
    
    return []




async def run():
    async with streamablehttp_client(mcp_server_url, auth=None) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # Fetch user info resource if available
            user_info = None
            try:
                user_resource = await session.read_resource("local://user")
                user_info = json.loads(user_resource.contents[0].text)
            except Exception as e:
                print(f"Could not fetch user resource: {e}")

            # List available tools
            tools = await session.list_tools()
            functions = []
            for tool in tools.tools:
                functions.append(convert_to_llm_tool(tool))

            # User prompt
            prompt = "יש לי 3 שטרות של 20$ ו-40 שטרות של 50$. כמה כסף יש לי?"
            # prompt = "מה השעה?"
            # prompt = "מי המציא את פייסבוק?"
            # prompt = "מה השטח העשרוני של מעגל עם רדיוס 3?"
            # prompt = "מה השם והגיל של המשתמש?"
            
            # Create the system prompt with the available tools
            system_prompt = create_system_prompt(functions, user_info)

            # Check if tools are needed
            print("\n--- Analyzing question ---")
            tool_calls = await call_llm(system_prompt, prompt)
            
            if not tool_calls:
                # No tools needed - generate direct answer
                print("No tools needed. Generating answer...")
                system_prompt = create_system_prompt(None, user_info)
                answer = await get_final_answer(system_prompt, prompt)
                print(f"\n✓ Answer: {answer}")
                
            else:
                # Tools needed - execute agentic loop
                print("Tools needed. Executing...")
                work_log = []

                max_iterations = 5
                iteration = 0
                done = False

                while not done and iteration < max_iterations:
                    print(f"\n--- Iteration {iteration + 1} ---")
                    
                    # Build user message with all previous work
                    if work_log:
                        user_message = f"Question: {prompt}\n\nCalculations completed:\n"
                        for step in work_log:
                            user_message += f"- {step['tool']}({step['args']}) = {step['result']}\n"
                        user_message += f"\nCurrent answer: {work_log[-1]['result']}"
                        user_message += '\n\nIf this answers the question, return []. Otherwise, call the next tool:'
                    else:
                        user_message = prompt

                    # Ask LLM what tools to call (system_prompt has tools, user_message is the question)
                    functions_to_call = await call_llm(system_prompt, user_message)

                    if not functions_to_call:
                        # Create answer system prompt (no tool instructions)
                        answer_system_prompt = create_system_prompt(None, user_info)
                        final_message = user_message.replace("If this answers the question, return []. Otherwise, call the next tool:", "")
                        answer = await get_final_answer(answer_system_prompt, final_message)
                        print("✓ Done! Final answer:", answer)
                        break
                    
                    # Execute first tool only
                    tool = functions_to_call[0]
                    
                    if not done:
                        result = await session.call_tool(tool["name"], arguments=tool["args"])
                        tool_result = result.content[0].text if result.content else "No result"
                        print(f"Result: {tool_result}")
                        
                        # Add this step to the work log
                        work_log.append({"tool": tool['name'], "args": tool['args'], "result": tool_result})
                    
                    iteration += 1


if __name__ == "__main__":
    import asyncio
    asyncio.run(run())
