"""
MCP Integration Service for Chat
Provides tools integration using Model Context Protocol with native function calling
"""
import json
import logging
from typing import List, Dict, Optional
from core.models import Message
from core.config import llm_config
from core.llm_engine import llm_engine
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

logger = logging.getLogger(__name__)


class MCPService:
    """Service for integrating MCP tools into chat using native function calling"""
    
    def __init__(self):
        self.mcp_server_url = f"{llm_config.mcp_url}/mcp"
        self.system_prompt = """
        אתה עוזר בינה מלאכותית שמטרתו לספק מידע מדויק ואמין בשפה העברית. ענה באופן ברור, מדויק, ומבוסס על עובדות בלבד.
         תמיד השתמש בכלים הזמינים כשהם רלוונטיים לשאלה.
         """
    
    
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
    
    async def process_with_mcp(self, user_prompt: str) -> Optional[List[Dict]]:
        """
        Process prompt with MCP tools using native function calling.
        Returns final messages or None if MCP not needed.
        """
        try:
            async with streamablehttp_client(self.mcp_server_url, auth=None) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # Get available tools from MCP
                    tools_discovered = await session.list_tools()
                    mcp_tools = tools_discovered.tools
                    if not mcp_tools:
                        return None
                    
                    logger.info(f"MCP tools: {[t.name for t in mcp_tools]}")
                    
                    # Format tools for vLLM
                    openai_tools = self.mcp_tools_to_openai(mcp_tools)
                    
                    # Build conversation with user prompt
                    messages = [
                        Message(role="system", content=self.system_prompt),
                        Message(role="user", content=user_prompt)
                    ]
                    
                    # Get non-streaming response to check for tool calls
                    response_data = await llm_engine.chat_completion(messages, session_id="mcp_llm_call", tools=openai_tools)
                    
                    # Extract the assistant message from response
                    if not response_data.get("choices") or len(response_data["choices"]) == 0:
                        logger.info("No response from LLM")
                        return None
                    
                    assistant_message = response_data["choices"][0]["message"]
                    tool_calls = assistant_message.get("tool_calls", [])
                                      
                    # Check if LLM wants to use tools
                    if not tool_calls:
                        logger.info("No tool calls requested by LLM")
                        return None
                    
                    # Execute tool calls
                    tool_results = []
                    for tool_call in tool_calls:
                        function = tool_call.get("function", {})
                        tool_name = function.get("name")
                        
                        # Parse arguments (may be string or dict)
                        args = function.get("arguments", {})
                        if isinstance(args, str):
                            try:
                                args = json.loads(args)
                            except json.JSONDecodeError:
                                args = {}
                        
                        result = await self._call_tool(session, tool_name, args)
                        logger.info(f"Called tool: {tool_name}({args}), Tool result: {result}")
                        
                        tool_results.append({
                            "tool_name": tool_name,
                            "result": result
                        })
                    
                    # Build context with tool results for final answer
                    tool_context = "\n".join([
                        f"כלי {tr['tool_name']}: {tr['result']}" 
                        for tr in tool_results
                    ])
                    
                    final_prompt = f"""שאלה: {user_prompt}

תוצאות מכלים:
{tool_context}

ענה על השאלה בהתבסס על התוצאות מהכלים."""
                    
                    return [
                        Message(role="system", content=self.system_prompt),
                        Message(role="user", content=final_prompt)
                    ]
                    
        except Exception as e:
            logger.warning(f"MCP processing error: {e}", exc_info=True)
            return None


# Global instance
mcp_service = MCPService()
