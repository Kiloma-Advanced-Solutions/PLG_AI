"""
MCP Integration Service for Chat
Provides tools integration to the chat system using Model Context Protocol
"""
import json
import logging
from typing import List, Dict, Any, Optional
from core.models import Message
from core.config import llm_config
from core.llm_engine import llm_engine
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

logger = logging.getLogger(__name__)


class MCPService:
    """Service for integrating MCP tools into chat conversations"""
    
    def __init__(self):
        self.mcp_server_url = f"{llm_config.mcp_url}/mcp"  # MCP server URL
        self.enabled = True  # Can be toggled based on configuration
        self._client_session = None
        self._tools_cache = None
        self._user_info_cache = None
    
    def create_system_prompt(self, functions: Optional[List[Dict]] = None, user_info: Optional[Dict] = None) -> str:
        """
        Create system prompt with optional tool definitions
        
        Args:
            functions: List of available tool schemas
            user_info: User information from MCP resources
            
        Returns:
            System prompt string
        """
        system_prompt = "אתה עוזר בינה מלאכותית שמטרתו לספק מידע מדויק ואמין בשפה העברית. ענה באופן ברור, מדויק, ומבוסס על עובדות בלבד."
        
        # Add user info if available
        if user_info:
            system_prompt += f"\n\nמידע על המשתמש:\n{json.dumps(user_info, ensure_ascii=False)}."
        
        # Add available tools information
        if functions:
            system_prompt += "\n\nיש לך גישה לכלים הבאים:\n"
            for func in functions:
                func_info = func["function"]
                system_prompt += f"\n- {func_info['name']}: {func_info['description']}\n"
                props = func_info['parameters']['properties']
                if props:
                    system_prompt += f"  ארגומנטים:\n"
                    for param_name, param_info in props.items():
                        param_type = param_info.get('type', 'any')
                        param_desc = param_info.get('description', '')
                        system_prompt += f"    - {param_name} ({param_type}): {param_desc}\n"
            
            system_prompt += "\n\nפורמט תשובה (החזר רק JSON, ללא הסברים):"
            system_prompt += '\n- לקריאת כלי: {"tool": "name", "arguments": {...}}'
            system_prompt += '\n- כאשר סיימת: []'
            system_prompt += "\n\nחשוב: החזר רק JSON - ללא טקסט, ללא הסברים."
        
        return system_prompt
    
    def convert_to_llm_tool(self, tool) -> Dict:
        """
        Convert MCP tool schema to LLM tool format
        
        Args:
            tool: MCP tool object
            
        Returns:
            Tool schema in LLM format
        """
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "type": "function",
                "parameters": {
                    "type": "object",
                    "properties": tool.inputSchema.get("properties", {})
                }
            }
        }
    
    async def get_llm_response(self, messages: List[Dict], session_id: str = "mcp_llm_call") -> str:
        """
        Get LLM response using llm_engine and collect full text
        
        Args:
            messages: List of message dictionaries
            session_id: Session ID for tracking
            
        Returns:
            Full response text
        """
        try:
            # Convert dict messages to Message objects
            message_objects = [
                Message(role=msg["role"], content=msg["content"])
                for msg in messages
            ]
            
            # Stream response from llm_engine and collect text
            full_response = ""
            async for chunk in llm_engine.chat_stream(message_objects, session_id):
                # Parse SSE format: "data: {json}\n\n"
                if chunk.startswith('data: '):
                    data = chunk[6:].strip()
                    
                    if data == '[DONE]':
                        break
                    
                    try:
                        parsed = json.loads(data)
                        if 'choices' in parsed and len(parsed['choices']) > 0:
                            content = parsed['choices'][0].get('delta', {}).get('content', '')
                            full_response += content
                    except json.JSONDecodeError:
                        pass
            
            return full_response.strip()
        except Exception as e:
            logger.warning(f"LLM response error in MCP: {e}")
            return ""
    
    async def call_llm_for_tools(self, system_prompt: str, prompt: str) -> List[Dict]:
        """
        Call LLM to determine which tools to use
        
        Args:
            system_prompt: System prompt with tool definitions
            prompt: User prompt or current question
            
        Returns:
            List of tool calls to make
        """
        logger.info("Calling LLM for tool decision...")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        
        full_response = await self.get_llm_response(messages, session_id="mcp_tool_decision")
        
        if not full_response:
            return []
        
        logger.info(f"LLM tool response: {full_response}")
        
        # Parse the response to extract tool calls
        try:
            # Clean response
            response_clean = full_response.replace('```json', '').replace('```', '').strip()
            
            # If [] in model response - Done, no more tool calls needed
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
            logger.warning(f"Could not parse tool response: {e}")
        
        return []
    
    async def get_final_answer(self, system_prompt: str, prompt: str) -> str:
        """
        Get final answer without tools
        
        Args:
            system_prompt: System prompt (without tool definitions)
            prompt: User question with context
            
        Returns:
            Final answer
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        return await self.get_llm_response(messages, session_id="mcp_final_answer")
    
    async def call_mcp_tool(self, session: ClientSession, tool_name: str, arguments: Dict) -> str:
        """
        Call an MCP tool via the MCP client session
        
        Args:
            session: MCP client session
            tool_name: Name of the tool to call
            arguments: Arguments for the tool
            
        Returns:
            Tool result as string
        """
        try:
            result = await session.call_tool(tool_name, arguments=arguments)
            if result.content and len(result.content) > 0:
                return result.content[0].text
            return "No result"
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {e}")
            return f"Error: {e}"
    
    async def get_available_tools(self, session: ClientSession) -> List[Dict]:
        """
        Get list of available tools from MCP server via session
        
        Args:
            session: MCP client session
            
        Returns:
            List of tool schemas
        """
        if self._tools_cache is not None:
            return self._tools_cache
        
        try:
            tools_result = await session.list_tools()
            tools = [self.convert_to_llm_tool(tool) for tool in tools_result.tools]
            self._tools_cache = tools
            return tools
        except Exception as e:
            logger.warning(f"Could not get tools from MCP server: {e}")
            return []
    
    async def get_user_info(self, session: ClientSession) -> Optional[Dict]:
        """
        Get user information from MCP resources via session
        
        Args:
            session: MCP client session
            
        Returns:
            User info dictionary or None
        """
        if self._user_info_cache is not None:
            return self._user_info_cache
        
        try:
            user_resource = await session.read_resource("local://user")
            if user_resource.contents and len(user_resource.contents) > 0:
                user_info = json.loads(user_resource.contents[0].text)
                self._user_info_cache = user_info
                return user_info
            return None
        except Exception as e:
            logger.debug(f"User resource not available: {e}")
            return None
    
    async def process_with_mcp(self, user_prompt: str) -> Optional[List[Dict]]:
        """
        Process user prompt with MCP tools if needed
        
        Args:
            user_prompt: User's message
            
        Returns:
            List of messages with tool results for final answer generation, or None if MCP not needed
        """
        try:
            # Connect to MCP server using streamable HTTP client
            async with streamablehttp_client(self.mcp_server_url, auth=None) as (read, write, get_session_id):
                async with ClientSession(read, write) as session:
                    # Initialize the connection
                    await session.initialize()
                    
                    # Get available tools
                    tools = await self.get_available_tools(session)
                    
                    if not tools:
                        logger.info("No MCP tools available, falling back to direct response")
                        return None  # Signal to use regular chat flow
                    
                    # Get user info
                    user_info = await self.get_user_info(session)
                    
                    # Create system prompt with tools
                    system_prompt_with_tools = self.create_system_prompt(tools, user_info)
                    
                    # Check if tools are needed
                    logger.info("Analyzing if tools are needed...")
                    tool_calls = await self.call_llm_for_tools(system_prompt_with_tools, user_prompt)
                    
                    if not tool_calls:
                        # No tools needed - return None to signal using regular chat
                        logger.info("No tools needed")
                        return None
                    
                    # Tools needed - execute agentic loop
                    logger.info("Tools needed, executing agentic loop")
                    work_log = []
                    max_iterations = 5
                    iteration = 0
                    
                    while iteration < max_iterations:
                        logger.info(f"Iteration {iteration + 1}")
                        
                        # Build user message with all previous work
                        if work_log:
                            user_message = f"שאלה: {user_prompt}\n\nחישובים שבוצעו:\n"
                            for step in work_log:
                                user_message += f"- {step['tool']}({step['args']}) = {step['result']}\n"
                            user_message += f"\n\nתשובה נוכחית: {work_log[-1]['result']}"
                            user_message += '\n\nאם זה עונה על השאלה, החזר []. אחרת, קרא לכלי הבא:'
                        else:
                            user_message = user_prompt
                        
                        # Ask LLM what tools to call
                        functions_to_call = await self.call_llm_for_tools(system_prompt_with_tools, user_message)
                        
                        if not functions_to_call:
                            # Done - return messages for final answer generation
                            logger.info("Agentic loop completed, returning context for streaming")
                            answer_system_prompt = self.create_system_prompt(None, user_info)
                            final_message = user_message.replace("אם זה עונה על השאלה, החזר []. אחרת, קרא לכלי הבא:", "")
                            
                            # Return messages for streaming by chat service
                            return [
                                {"role": "system", "content": answer_system_prompt},
                                {"role": "user", "content": final_message}
                            ]
                        
                        # Execute first tool only
                        tool = functions_to_call[0]
                        logger.info(f"Calling tool: {tool['name']} with args: {tool['args']}")
                        
                        tool_result = await self.call_mcp_tool(session, tool["name"], tool["args"])
                        logger.info(f"Tool result: {tool_result}")
                        
                        # Add this step to the work log
                        work_log.append({"tool": tool['name'], "args": tool['args'], "result": tool_result})
                        
                        iteration += 1
                    
                    # Max iterations reached - return best context so far
                    logger.warning("Max iterations reached in agentic loop")
                    if work_log:
                        answer_system_prompt = self.create_system_prompt(None, user_info)
                        context_message = f"שאלה: {user_prompt}\n\nחישובים שבוצעו:\n"
                        for step in work_log:
                            context_message += f"- {step['tool']}({step['args']}) = {step['result']}\n"
                        context_message += f"\n\nתשובה נוכחית: {work_log[-1]['result']}\n\nבבקשה סכם את התוצאה הסופית."
                        
                        return [
                            {"role": "system", "content": answer_system_prompt},
                            {"role": "user", "content": context_message}
                        ]
                    return None
                    
        except Exception as e:
            logger.warning(f"MCP connection error: {e}")
            return None
    
    def clear_cache(self):
        """Clear cached tools and user info"""
        self._tools_cache = None
        self._user_info_cache = None


# Global MCP service instance
mcp_service = MCPService()

