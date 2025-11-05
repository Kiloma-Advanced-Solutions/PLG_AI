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
                logger.info(f"Running triage for: {latest_user_msg[:100]}")

                try:
                    # Run triage agent to decide routing
                    triage_result = await Runner().run(triage_agent, latest_user_msg)
                    
                    # Extract JSON from markdown code blocks if present
                    raw_output = triage_result.final_output.strip()
                    
                    # Remove markdown code blocks (```json ... ``` or ``` ... ```)
                    if raw_output.startswith("```"):
                        # Extract content between triple backticks
                        match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', raw_output, re.DOTALL)
                        if match:
                            raw_output = match.group(1).strip()
                    
                    logger.info(f"Triage output: {raw_output[:200]}")
                    
                    triage_data = json.loads(raw_output)
                    triage_response = TriageAgentResponse(**triage_data)

                    logger.info(
                        f"Triage decision: handoff={triage_response.should_handoff}, "
                        f"agent={triage_response.handoff_agent if triage_response.should_handoff else 'general'}"
                    )

                    # Route to selected agent based on triage decision
                    if triage_response.should_handoff:
                        agent_name = triage_response.handoff_agent.lower()
                        if agent_name == "io":
                            selected_agent = io_agent
                        elif agent_name == "internet":
                            selected_agent = internet_agent
                        else:
                            selected_agent = general_agent
                    else:
                        selected_agent = general_agent

                    logger.info(f"Routing to {selected_agent.name}")

                    # Ensure MCP servers are connected before streaming
                    await self.ensure_mcp_servers_connected(
                        getattr(selected_agent, "mcp_servers", [])
                    )

                    # Stream the selected agent's response
                    runner = Runner()
                    
                    # Wrap MCP servers to reconnect before each call_tool (workaround for ClosedResourceError)
                    original_call_tools = {}
                    for mcp_server in getattr(selected_agent, "mcp_servers", []):
                        original_call_tool = mcp_server.call_tool
                        async def logged_call_tool(tool_name: str, arguments: dict, _orig=original_call_tool, _server=mcp_server):
                            try:
                                # Reconnect before each tool call to work around session closure
                                logger.info(f"[MCP] Reconnecting to {_server.name} before calling {tool_name}")
                                try:
                                    await _server.cleanup()
                                except Exception:
                                    pass  # Ignore cleanup errors
                                await _server.connect()
                                
                                logger.info(f"[MCP] Calling tool {tool_name} with args: {arguments}")
                                result = await _orig(tool_name, arguments)
                                logger.info(f"[MCP] Tool {tool_name} returned: {result}")
                                return result
                            except Exception as e:
                                logger.error(f"[MCP] Tool {tool_name} failed: {type(e).__name__}: {e}", exc_info=True)
                                raise
                        mcp_server.call_tool = logged_call_tool
                        original_call_tools[id(mcp_server)] = original_call_tool
                    
                    result = runner.run_streamed(selected_agent, latest_user_msg)
                    tool_arg_buffers: Dict[str, str] = {}

                    async for event in result.stream_events():
                        logger.debug(
                            "Stream event received: %s",
                            getattr(event, "type", "unknown"),
                        )

                        if event.type == "raw_response_event":
                            response_event = event.data
                            event_type = getattr(response_event, "type", "")
                            logger.debug("Raw response event type: %s", event_type)

                            if event_type == "response.output_text.delta":
                                chunk = getattr(response_event, "delta", "")
                                if not chunk:
                                    continue

                                payload = {
                                    "choices": [
                                        {
                                            "delta": {
                                                "content": chunk
                                            }
                                        }
                                    ]
                                }
                                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

                            elif event_type == "response.function_call_arguments.delta":
                                # Stream argument deltas for visibility during debugging
                                delta = getattr(response_event, "arguments_delta", "")
                                tool_id = getattr(response_event, "tool_call_id", None)
                                if tool_id:
                                    tool_arg_buffers[tool_id] = (
                                        tool_arg_buffers.get(tool_id, "") + (delta or "")
                                    )
                                logger.info(
                                    "Tool argument delta received: id=%s delta=%s buffer=%s",
                                    tool_id,
                                    delta,
                                    tool_arg_buffers.get(tool_id, ""),
                                )

                            elif event_type == "response.completed":
                                yield "data: [DONE]\n\n"
                                return

                        elif event.type == "run_item_stream_event":
                            item = getattr(event, "item", None)
                            item_type = getattr(item, "type", "") if item else ""
                            logger.debug(
                                "Run item event name=%s type=%s",
                                getattr(event, "name", "unknown"),
                                item_type,
                            )

                            if item_type == "tool_call_item" and item is not None:
                                raw_item = getattr(item, "raw_item", None)
                                tool_name = getattr(raw_item, "name", None)
                                arguments = getattr(raw_item, "arguments", None)
                                tool_call_id = getattr(raw_item, "id", None)
                                buffered_args = (
                                    tool_arg_buffers.get(tool_call_id, "") if tool_call_id else None
                                )
                                logger.info(
                                    "Tool call issued: name=%s id=%s arguments=%s buffered_arguments=%s",
                                    tool_name,
                                    tool_call_id,
                                    arguments,
                                    buffered_args,
                                )

                            if item_type == "tool_call_output_item" and item is not None:
                                tool_output = getattr(item, "output", None)
                                logger.info(
                                    "Tool call output received",
                                    extra={
                                        "output": tool_output,
                                        "raw": getattr(item, "raw_item", None),
                                    },
                                )
                                
                                # Stream the tool output directly to the user
                                if tool_output:
                                    output_text = str(tool_output)
                                    payload = {
                                        "choices": [
                                            {
                                                "delta": {
                                                    "content": output_text
                                                }
                                            }
                                        ]
                                    }
                                    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                                    # Send done signal and exit
                                    yield "data: [DONE]\n\n"
                                    return

                            if item_type == "message_output_item" and item is not None:
                                raw_message = getattr(item, "raw_item", None)
                                if raw_message is None:
                                    continue

                                content_parts = getattr(raw_message, "content", [])
                                for content_part in content_parts:
                                    part_type = getattr(content_part, "type", "")
                                    text_value = getattr(content_part, "text", None)

                                    if part_type == "output_text" and text_value:
                                        payload = {
                                            "choices": [
                                                {
                                                    "delta": {
                                                        "content": text_value
                                                    }
                                                }
                                            ]
                                        }
                                        yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

                            else:
                                logger.debug(
                                    "Run item event: %s for agent %s",
                                    getattr(event, "name", "unknown"),
                                    selected_agent.name,
                                )

                    # If we exit the loop without a completion event, send done signal
                    yield "data: [DONE]\n\n"
                    return  # Exit after agent handles the request
                    
                except Exception as triage_error:
                    logger.exception(
                        "Triage failed, falling back to regular chat: %s",
                        repr(triage_error),
                    )
                    # Fall through to regular chat processing

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
        """
        Extract the most recent user message from conversation
        
        Args:
            messages: Conversation history
            
        Returns:
            Latest user message content or None
        """
        for msg in reversed(messages):
            if msg.role == "user":
                return msg.content.strip()
        return None

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