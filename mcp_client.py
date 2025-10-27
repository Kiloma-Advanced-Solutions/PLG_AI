
"""
MCP Integration Service for Chat
Provides tools integration using Model Context Protocol with native function calling
"""
import json
import logging
import os
from typing import List, Dict, Optional
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class MCPService:
    """Service for integrating MCP tools into chat using native function calling"""
    
    def __init__(self):
        # Multiple MCP servers
        self.mcp_servers = [
            os.getenv("MCP_SERVER_URL", "http://localhost:8000/mcp"),  # Time server
            # os.getenv("GMAIL_MCP_SERVER_URL", "http://localhost:8002")  # Gmail server - temporarily disabled
        ]
        self.system_prompt = """
        אתה עוזר בינה מלאכותית שמטרתו לספק מידע מדויק ואמין בשפה העברית. ענה באופן ברור, מדויק, ומבוסס על עובדות בלבד.
         תמיד השתמש בכלים הזמינים כשהם רלוונטיים לשאלה.
         """
        # Initialize OpenAI client
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    
    # Convert MCP tool schema to OpenAI style
    def mcp_tools_to_openai(self, mcp_tools: List) -> List[Dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            }
        for tool in mcp_tools]

    
    
    async def _call_tool(self, session: ClientSession, tool_name: str, args: Dict) -> str:
        """Execute MCP tool"""
        try:
            result = await session.call_tool(tool_name, arguments=args)
            return result.content[0].text if result.content else "No result"
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return f"Error: {e}"
    
    async def _get_tools_from_server(self, server_url: str):
        """Helper to get list of tools from an MCP server"""
        async with streamablehttp_client(server_url, auth=None) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_discovered = await session.list_tools()
                return tools_discovered.tools
    
    async def _call_tool_on_server(self, server_url: str, tool_name: str, args: dict):
        """Helper to call a tool on an MCP server"""
        async with streamablehttp_client(server_url, auth=None) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await self._call_tool(session, tool_name, args)
                return result
    
    async def process_with_mcp(self, user_prompt: str) -> Optional[List[Dict]]:
        """
        Process prompt with MCP tools using native function calling.
        Returns final messages or None if MCP not needed.
        """
        try:
            all_tools = []
            server_tools_map = {}  # Maps server_url -> list of tool names
            
            # Connect to all MCP servers and collect tools
            for server_url in self.mcp_servers:
                try:
                    logger.info(f"Attempting to connect to MCP server: {server_url}")
                    mcp_tools = await self._get_tools_from_server(server_url)
                    
                    if mcp_tools:
                        logger.info(f"MCP tools from {server_url}: {[t.name for t in mcp_tools]}")
                        all_tools.extend(mcp_tools)
                        server_tools_map[server_url] = [t.name for t in mcp_tools]
                    else:
                        logger.warning(f"No tools found on {server_url}")
                    
                except Exception as e:
                    logger.error(f"Failed to connect to MCP server {server_url}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            if not all_tools:
                logger.info("No MCP tools available")
                return None
            
            logger.info(f"Total MCP tools available: {[t.name for t in all_tools]}")
            
            # Format tools for OpenAI
            openai_tools = self.mcp_tools_to_openai(all_tools)
            
            # Build conversation with user prompt
            messages = [
                {"role":"system", "content":self.system_prompt},
                {"role":"user", "content":user_prompt}
            ]
            
            # Get non-streaming response to check for tool calls
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                tools=openai_tools,
                tool_choice="auto"
            )
            
            # Extract the assistant message from response
            if not response.choices or len(response.choices) == 0:
                logger.info("No response from OpenAI")
                return None
            
            assistant_message = response.choices[0].message
            tool_calls = assistant_message.tool_calls or []
                          
            # Check if LLM wants to use tools
            if not tool_calls:
                logger.info("No tool calls requested by LLM")
                return None
            
            # Execute tool calls
            tool_results = []
            for tool_call in tool_calls:
                function = tool_call.function
                tool_name = function.name
                
                # Parse arguments (may be string or dict)
                args = function.arguments
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}
                
                # Find which server has this tool and call it
                for server_url, tool_names in server_tools_map.items():
                    if tool_name in tool_names:
                        try:
                            result = await self._call_tool_on_server(server_url, tool_name, args)
                            logger.info(f"Called tool: {tool_name}({args}), Tool result: {result}")
                            tool_results.append({
                                "tool_name": tool_name,
                                "result": result
                            })
                        except Exception as e:
                            logger.error(f"Failed to call tool {tool_name}: {e}")
                        break
            
            if not tool_results:
                return None
            
            # Build context with tool results for final answer
            tool_context = "\n".join([
                f"כלי {tr['tool_name']}: {tr['result']}" 
                for tr in tool_results
            ])
            
            final_prompt = f"""שאלה: {user_prompt}

תוצאות מכלים:
{tool_context}

ענה על השאלה בהתבסס על התוצאות מהכלים."""
            
            # Get final response from OpenAI
            final_messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": final_prompt}
            ]
            
            final_response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=final_messages
            )
            
            final_answer = final_response.choices[0].message.content
            
            return [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": final_answer}
            ]
            
        except Exception as e:
            logger.warning(f"MCP processing error: {e}", exc_info=True)
            import traceback
            traceback.print_exc()
            return None


# Global instance
mcp_service = MCPService()

async def test_mcp():
    """Test the MCP service with a simple query"""
    test_prompt = "מה השעה?"
    print(f"Testing MCP with prompt: {test_prompt}")
    
    result = await mcp_service.process_with_mcp(test_prompt)
    if result:
        print("MCP processing successful!")
        for message in result:
            print(f"{message['role']}: {message['content']}")
    else:
        print("MCP processing returned None")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_mcp())
