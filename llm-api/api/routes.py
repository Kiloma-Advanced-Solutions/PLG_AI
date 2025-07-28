# api/routes.py - HTTP Endpoints
"""
API routes and endpoint handlers
"""

import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse

from core.models import ChatRequest, HealthStatus
from services.chat_service import chat_service
from utils.health import health_checker
from services.task_service import TaskService
from core.models import TaskExtractionRequest, TaskExtractionResponse

logger = logging.getLogger(__name__)

def create_routes(app: FastAPI) -> None:
    """Configure all API routes with proper error handling"""
    
    # ===============================
    # CHAT ENDPOINT
    # ===============================
    
    @app.post("/api/chat/stream")
    async def stream_chat(request: Request):
        """
        Chat streaming endpoint
        
        Accepts chat requests and returns real-time streaming responses
        """
        try:
            body = await request.json()         # Extract JSON data from HTTP request body
            chat_request = ChatRequest(**body)  # Create ChatRequest object from JSON data, with automatic validation
            
            # Generate session ID if not provided
            session_id = chat_request.session_id or chat_service.generate_session_id()
            
            # Log chat request
            user_msg = chat_service.extract_latest_user_message(chat_request.messages)
            logger.info(f"Chat request - User: {user_msg}")
            
            # Stream chat response
            return StreamingResponse(
                # Call chat service to generate response stream
                chat_service.stream_chat(chat_request.messages, session_id),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "X-Session-ID": session_id
                }
            )
            
        except HTTPException:
            raise
        except ValueError as e:
            logger.warning(f"Chat validation error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Chat endpoint error: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Chat service temporarily unavailable"
            )
    
    # ===============================
    # HEALTH MONITORING ENDPOINTS
    # ===============================
    
    @app.get("/api/health", response_model=HealthStatus)
    async def health_check() -> HealthStatus:
        """
        System health check endpoint
        
        Returns comprehensive health status including vLLM connectivity
        """
        try:
            health_status = await health_checker.check_system_health()
            
            # Log health issues
            if health_status.status == "unhealthy":
                logger.warning("System health check failed")
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            # Return unhealthy status on any error
            return HealthStatus(
                status="unhealthy",
                vllm_healthy=False,
                active_sessions=0
            )
    
    @app.post("/tasks/extract", response_model=TaskExtractionResponse)
    async def extract_tasks(request: TaskExtractionRequest) -> TaskExtractionResponse:
        """
        Extract tasks from email content.
        
        Args:
            request: TaskExtractionRequest containing the email content
            
        Returns:
            TaskExtractionResponse containing extracted tasks
        """
        try:
            task_service = TaskService()
            tasks = await task_service.extract_tasks(request.email_content)
            return TaskExtractionResponse(tasks=tasks)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to extract tasks: {str(e)}"
            )
    
    