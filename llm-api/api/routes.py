# api/routes.py - HTTP Endpoints
"""
API endpoints and request routing
"""

import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from core.models import HealthStatus, ChatRequest, TitleGenerationRequest, TitleGenerationResponse, TaskExtractionRequest, TaskExtractionResponse, EmailSummarizationRequest, EmailSummary
from utils.health import health_checker
from services.chat_service import chat_service
from services.task_service import task_service
from services.title_service import title_service
from services.summarization_service import summarization_service

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

            # Extract latest user message
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
    # TASK EXTRACTION ENDPOINT
    # ===============================
    
    @app.post("/api/tasks/extract", response_model=TaskExtractionResponse)
    async def extract_tasks(request: TaskExtractionRequest) -> TaskExtractionResponse:
        """
        Extract tasks from email content.
        
        Args:
            request: TaskExtractionRequest containing the email content
            
        Returns:
            TaskExtractionResponse containing extracted tasks
        """
        try:
            result = await task_service.extract_tasks(request.email_content)
            return result
        except Exception as e:
            logger.error(f"Task extraction error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to extract tasks: {e}"
            )
        
    
    # ===============================
    # TITLE GENERATION ENDPOINT
    # ===============================
    
    @app.post("/api/title/generate", response_model=TitleGenerationResponse)
    async def generate_title(request: TitleGenerationRequest) -> TitleGenerationResponse:
        """
        Generate an up to 6-word conversation title from user message.
        
        Args:
            request: TitleGenerationRequest containing the user message
            
        Returns:
            TitleGenerationResponse containing the generated title
        """
        try:
            result = await title_service.generate_title(request.user_message)
            return result
        except Exception as e:
            logger.error(f"Title generation error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate title: {e}"
            )
    


    # ===============================
    # EMAIL SUMMARIZATION ENDPOINT
    # ===============================
    
    @app.post("/api/summarization/summarize", response_model=EmailSummary)
    async def summarize_email(request: EmailSummarizationRequest) -> EmailSummary:
        """
        Summarize an email according to a given length.
        
        Args:
            request: EmailSummarizationRequest containing the email content and the required summary length
            
        Returns:
            EmailSummary containing the summary of the email
        """
        try:
            result = await summarization_service.summarize_email(request.email_content, request.length)
            return result
        except Exception as e:
            logger.error(f"Failed to summarize email: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to summarize email: {e}"
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
    
