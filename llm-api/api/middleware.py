"""
CORS, security, and request processing
"""
import logging
from typing import Callable
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import llm_config

logger = logging.getLogger(__name__)

def setup_middleware(app: FastAPI) -> None:
    """Configure all middleware for the API"""
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=llm_config.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next: Callable) -> Response:
        """Log all incoming requests"""
        try:
            response = await call_next(request)  # calls the actual endpoint
            logger.info(f"{request.method} {request.url.path} - {response.status_code}")
            return response
        except Exception as e:
            logger.error(f"Request error: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error"}
            )
    
    # Error handling middleware
    @app.middleware("http")
    async def catch_exceptions(request: Request, call_next: Callable) -> Response:
        """Global exception handler"""
        try:
            return await call_next(request)
        except Exception as e:
            logger.error(f"Unhandled error: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "An unexpected error occurred"}
            ) 