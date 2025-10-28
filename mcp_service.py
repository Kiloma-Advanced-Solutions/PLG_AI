"""
MCP Integration Service for Chat
Supports multiple MCP servers with tool aggregation
"""
import asyncio
import json
import logging
import subprocess
from typing import List, Optional
from config import llm_config
from llm_engine import llm_engine
from models import Message
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.stdio import stdio_client, StdioServerParameters

logger = logging.getLogger(__name__)

class MCPService:
    """Service for integrating MCP tools from multiple servers"""
    
    def __init__(self):
        # Support multiple MCP servers
        self.mcp_servers = llm_config.mcp_servers
        self.stdio_servers = {
            "google-flights": {
                "command": "myenv/bin/python",
                "args": ["Google-Flights-MCP-Server/server.py"]
            }
        }
        self.server_tool_map = {}  # tool_name -> server_config
        self.system_prompt = """אתה עוזר בינה מלאכותית שמטרתו לספק מידע מדויק ואמין בשפה העברית. ענה באופן ברור, מדויק, ומבוסס על עובדות בלבד. תמיד השתמש בכלים הזמינים כשהם רלוונטיים לשאלה."""
        logger.info(f"Initialized MCPService with HTTP servers: {self.mcp_servers}")
        logger.info(f"Initialized MCPService with stdio servers: {list(self.stdio_servers.keys())}")
    
    async def _get_tools_from_http_server(self, server_url: str) -> List[dict]:
        """Get tools from an HTTP server"""
        try:
            async with streamablehttp_client(f"{server_url}/mcp", auth=None) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    
                    result = []
                    for tool in tools.tools:
                        self.server_tool_map[tool.name] = {"type": "http", "url": server_url}
                        result.append({
                            "type": "function",
                            "function": {
                                "name": tool.name,
                                "description": tool.description,
                                "parameters": tool.inputSchema,
                            },
                        })
                    
                    logger.info(f"HTTP {server_url}: {len(result)} tools")
                    return result
        except Exception as e:
            logger.warning(f"HTTP {server_url}: {e}")
            return []
    
    async def _get_tools_from_stdio_server(self, server_name: str, server_config: dict) -> List[dict]:
        """Get tools from a stdio server"""
        try:
            server_params = StdioServerParameters(
                command=server_config["command"],
                args=server_config["args"]
            )
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    
                    result = []
                    for tool in tools.tools:
                        self.server_tool_map[tool.name] = {"type": "stdio", "name": server_name, "config": server_config}
                        result.append({
                            "type": "function",
                            "function": {
                                "name": tool.name,
                                "description": tool.description,
                                "parameters": tool.inputSchema,
                            },
                        })
                    
                    logger.info(f"STDIO {server_name}: {len(result)} tools")
                    return result
        except Exception as e:
            logger.warning(f"STDIO {server_name}: {e}")
            return []
    
    async def _execute_tool(self, tool_name: str, args: dict) -> str:
        """Execute tool on its server"""
        server_config = self.server_tool_map.get(tool_name)
        if not server_config:
            return f"Error: Tool {tool_name} not found"
        
        try:
            if server_config["type"] == "http":
                # Execute on HTTP server
                async with streamablehttp_client(f"{server_config['url']}/mcp", auth=None) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.call_tool(tool_name, arguments=args)
                        return result.content[0].text if result.content else "No result"
            
            elif server_config["type"] == "stdio":
                # Execute on stdio server
                server_params = StdioServerParameters(
                    command=server_config["config"]["command"],
                    args=server_config["config"]["args"]
                )
                async with stdio_client(server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.call_tool(tool_name, arguments=args)
                        return result.content[0].text if result.content else "No result"
            
            else:
                return f"Error: Unknown server type for tool {tool_name}"
                
        except Exception as e:
            return f"Error executing {tool_name}: {e}"
    
    async def process_with_mcp(self, user_prompt: str) -> Optional[List[Message]]:
        """Process with MCP tools"""
        try:
            # Get all tools from all servers
            all_tools = []
            
            # Get tools from HTTP servers
            for server in self.mcp_servers:
                all_tools.extend(await self._get_tools_from_http_server(server))
            
            # Get tools from stdio servers
            for server_name, server_config in self.stdio_servers.items():
                all_tools.extend(await self._get_tools_from_stdio_server(server_name, server_config))
            
            if not all_tools:
                return None
            
            # Query LLM
            messages = [Message(role="system", content=self.system_prompt), Message(role="user", content=user_prompt)]
            response = await llm_engine.chat_completion(messages, session_id="mcp", tools=all_tools)
            
            tool_calls = response.get("choices", [{}])[0].get("message", {}).get("tool_calls", [])
            if not tool_calls:
                return None
            
            # Execute tools
            results = []
            for call in tool_calls:
                fn = call.get("function", {})
                args = fn.get("arguments", {})
                if isinstance(args, str):
                    args = json.loads(args)
                
                result = await self._execute_tool(fn.get("name"), args)
                results.append(f"Tool {fn.get('name')}: {result}")
            
            # Return final prompt
            final = f"שאלה: {user_prompt}\n\nתוצאות מכלים:\n" + "\n".join(results) + "\n\nענה על השאלה בהתבסס על התוצאות."
            return [Message(role="system", content=self.system_prompt), Message(role="user", content=final)]
            
        except Exception as e:
            logger.error(f"MCP error: {e}")
            return None


# Global instance
mcp_service = MCPService()
