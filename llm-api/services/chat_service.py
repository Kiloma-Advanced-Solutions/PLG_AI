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
        
        # Run triage agent
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
        """Run agent with MCP tools - SDK handles everything automatically."""
        logger.info(f"Running {agent.name}")
        
        # Let the SDK handle the full agent workflow
        result = await Runner().run(starting_agent=agent, input=user_message)
        
        # Stream the final output character by character
        if output := result.final_output:
            for char in output:
                yield self._sse(char)
                await asyncio.sleep(0.005)  # Small delay for smooth streaming
        
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
            session = getattr(server, "session", None)
            
            # Check if we need to reconnect
            needs_reconnect = False
            if session is None:
                needs_reconnect = True
            else:
                # Check if session is closed by trying to access write stream
                try:
                    write_stream = getattr(session, "_write_stream", None)
                    if write_stream is None or getattr(write_stream, "_closed", False):
                        needs_reconnect = True
                except:
                    needs_reconnect = True
            
            if needs_reconnect:
                # Cleanup old session if it exists
                if session is not None:
                    try:
                        await server.cleanup()
                    except:
                        pass
                
                logger.info(f"Connecting to MCP server {server.name}: {getattr(server, 'params', {}).get('url', 'unknown')}")
                await server.connect()
            else:
                logger.debug(f"MCP server {server.name} already connected, reusing session")


# Global chat service instance
chat_service = ChatService() 