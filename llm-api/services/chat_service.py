"""
Chat service for handling chat conversations
"""
import uuid
import logging
import json
import re
import asyncio
from typing import List, Optional, AsyncGenerator, Dict, Any
from agents.mcp import MCPServer
from core.llm_engine import llm_engine
from core.models import Message, TriageAgentResponse
from services.agent_service import triage_agent, io_agent, internet_agent, general_agent, Runner

logger = logging.getLogger(__name__)

class ChatService:
    """Service for handling chat conversations"""

    # Default system prompt for chat
    CHAT_SYSTEM_PROMPT = """אתה עוזר בינה מלאכותית שמטרתו לספק מידע מדויק ואמין בשפה העברית. ענה באופן ברור, מדויק, ומבוסס על עובדות בלבד. אל תנחש – אם אינך בטוח בתשובה, כתוב שאתה לא יודע או שהמידע חסר."""

    def __init__(self):
        """Initialize the chat service"""
        self.engine = llm_engine

    def generate_session_id(self) -> str:
        """Generate a unique session ID for chat sessions"""
        return f"chat_{uuid.uuid4().hex[:12]}"

    async def stream_chat(
        self,
        messages: List[Message],
        session_id: str,
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat responses with validation and error handling

        Args:
            messages: List of Message objects in conversation
            session_id: Session ID for tracking

        Yields:
            Server-sent event formatted strings
        """
        try:
            # Extract latest user message for triage
            latest_user_msg = self.extract_latest_user_message(messages)

            if latest_user_msg:
                try:
                    # Triage and route to appropriate agent
                    agent = await self._select_agent(latest_user_msg)
                    await self.ensure_mcp_servers_connected(getattr(agent, "mcp_servers", []))
                    
                    # Stream agent response
                    async for chunk in self._stream_agent_response(agent, latest_user_msg):
                        yield chunk
                    return
                    
                except Exception as e:
                    logger.exception(f"Agent routing failed: {e}")
                    # Fall through to regular chat

            # Fallback: regular chat stream
            async for chunk in self.engine.chat_stream(messages, session_id):
                yield chunk

        except ValueError as e:
            logger.warning(f"Chat validation error: {str(e)}")
            yield f'data: {{"error": "Invalid message format"}}\n\n'

        except Exception as e:
            logger.error(f"Chat service error: {str(e)}")
            yield f'data: {{"error": "Chat service unavailable"}}\n\n'

    

    def extract_latest_user_message(self, messages: List[Message]) -> Optional[str]:
        """Extract the most recent user message."""
        for msg in reversed(messages):
            if msg.role == "user":
                return msg.content.strip()
        return None
    
    async def _select_agent(self, user_message: str) -> Any:
        """Run triage and select appropriate agent."""
        logger.info(f"Triage: {user_message[:50]}...")
        
        # Run triage
        result = await Runner().run(triage_agent, user_message)
        raw = result.final_output.strip()
        
        # Extract JSON from markdown if needed
        if raw.startswith("```"):
            if match := re.search(r'```(?:json)?\s*\n?(.*?)\n?```', raw, re.DOTALL):
                raw = match.group(1).strip()
        
        # Parse triage decision
        triage = TriageAgentResponse(**json.loads(raw))
        logger.info(f"→ {triage.handoff_agent if triage.should_handoff else 'general'}")
        
        # Select agent
        if not triage.should_handoff:
            return general_agent
        
        agent_map = {"io": io_agent, "internet": internet_agent}
        return agent_map.get(triage.handoff_agent.lower(), general_agent)
    
    @staticmethod
    def _extract_text_from_tool_result(result: Any) -> Optional[str]:
        """Extract text content from MCP tool result."""
        if not result:
            return None
        
        # Try to extract from content items
        for item in getattr(result, 'content', []):
            if text := getattr(item, 'text', None):
                return text
        
        return str(result)
    
    @staticmethod
    def _sse(content: str) -> str:
        """Create SSE payload."""
        return f'data: {json.dumps({"choices": [{"delta": {"content": content}}]}, ensure_ascii=False)}\n\n'
    
    async def _stream_agent_response(self, agent: Any, user_message: str) -> AsyncGenerator[str, None]:
        """Stream agent responses with tool support."""
        # For agents with MCP tools, use non-streaming mode to avoid template errors
        if getattr(agent, "mcp_servers", []):
            async for chunk in self._run_agent_with_tools(agent, user_message):
                yield chunk
        else:
            # For agents without tools, use streaming
            result = Runner().run_streamed(agent, user_message)
            async for event in result.stream_events():
                if event.type == "raw_response_event":
                    if chunk := self._handle_raw_event(event):
                        yield chunk
                        if chunk == "data: [DONE]\n\n":
                            return
                elif event.type == "run_item_stream_event":
                    async for chunk in self._handle_item_event(event):
                        yield chunk
                        if chunk == "data: [DONE]\n\n":
                            return
            yield "data: [DONE]\n\n"
    
    async def _run_agent_with_tools(self, agent: Any, user_message: str) -> AsyncGenerator[str, None]:
        """
        Run agent with tools using manual tool execution loop.
        """
        from openai import AsyncOpenAI
        
        # Get the model's OpenAI client
        openai_client = agent.model._client  # Private attribute
        model_name = agent.model.model
        
        # Wrap MCP tool calls for reconnection
        mcp_servers = getattr(agent, "mcp_servers", [])
        for server in mcp_servers:
            original = server.call_tool
            async def wrapped(name: str, args: dict, _orig=original, _srv=server):
                logger.info(f"[MCP] {_srv.name}.{name}({args})")
                try:
                    await _srv.cleanup()
                except:
                    pass
                await _srv.connect()
                result = await _orig(name, args)
                logger.info(f"[MCP] {name} returned: {result}")
                return result
            server.call_tool = wrapped
        
        # Get tools from MCP servers (reconnect first if needed)
        tools = []
        for server in mcp_servers:
            # Ensure connection before listing tools
            try:
                await server.cleanup()
            except:
                pass
            await server.connect()
            server_tools = await server.list_tools()
            for tool in server_tools:
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.inputSchema or {"type": "object", "properties": {}}
                    }
                })
        
        logger.info(f"Running {agent.name} with {len(tools)} tools")
        
        # Step 1: Get tool call from LLM
        messages = [
            {"role": "system", "content": agent.instructions},
            {"role": "user", "content": user_message}
        ]
        
        response = await openai_client.chat.completions.create(
            model=model_name,
            messages=messages,
            tools=tools,
            tool_choice="required"
        )
        
        tool_calls = response.choices[0].message.tool_calls
        if not tool_calls:
            logger.warning("No tool calls generated")
            yield "data: [DONE]\n\n"
            return
        
        # Step 2: Execute tool
        tool_call = tool_calls[0]
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)
        
        logger.info(f"Executing tool: {tool_name}({tool_args})")
        
        # Find the right server and execute
        tool_result = None
        for server in mcp_servers:
            try:
                tool_result = await server.call_tool(tool_name, tool_args)
                break
            except:
                continue
        
        if not tool_result:
            logger.error(f"Tool {tool_name} execution failed")
            yield "data: [DONE]\n\n"
            return
        
        # Extract text from tool result
        tool_output = self._extract_text_from_tool_result(tool_result)
        logger.info(f"Tool output: {tool_output}")
        
        # Step 3: Get final response from LLM (without tool role)
        # Add assistant message acknowledging tool use, then user message with result
        # This maintains the required user/assistant alternation
        messages.append({
            "role": "assistant",
            "content": f"I'll use the {tool_name} tool to answer your question."
        })
        messages.append({
            "role": "user",
            "content": f"The tool returned: {tool_output}\n\nNow please provide a natural, helpful response in Hebrew."
        })
        
        response = await openai_client.chat.completions.create(
            model=model_name,
            messages=messages,
            stream=True
        )
        
        # Step 4: Stream the response
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield self._sse(chunk.choices[0].delta.content)
        
        yield "data: [DONE]\n\n"
    
    def _handle_raw_event(self, event: Any) -> Optional[str]:
        """Handle raw response events."""
        evt = event.data
        evt_type = getattr(evt, "type", "")
        
        if evt_type == "response.output_text.delta":
            if chunk := getattr(evt, "delta", ""):
                return self._sse(chunk)
        elif evt_type == "response.completed":
            return "data: [DONE]\n\n"
        
        return None
    
    async def _handle_item_event(self, event: Any) -> AsyncGenerator[str, None]:
        """Handle run item events."""
        if not (item := getattr(event, "item", None)):
            return
        
        item_type = getattr(item, "type", "")
        
        # Tool output
        if item_type == "tool_call_output_item":
            if text := self._extract_text_from_tool_result(getattr(item, "output", None)):
                logger.info(f"Tool output: {text[:50]}...")
                yield self._sse(text)
                yield "data: [DONE]\n\n"
        
        # Message output
        elif item_type == "message_output_item":
            if msg := getattr(item, "raw_item", None):
                for part in getattr(msg, "content", []):
                    if getattr(part, "type", "") == "output_text":
                        if text := getattr(part, "text", None):
                            yield self._sse(text)

    async def ensure_mcp_servers_connected(self, mcp_servers: List[MCPServer]) -> None:
        """Ensure all MCP servers have active sessions before use."""
        for server in mcp_servers:
            # Only connect if not already connected
            if getattr(server, "session", None) is None:
                logger.info(f"Connecting to MCP server {server.name}: {getattr(server, 'params', {}).get('url', 'unknown')}")
                await server.connect()
            else:
                logger.debug(f"MCP server {server.name} already connected, reusing session")


# Global chat service instance
chat_service = ChatService() 