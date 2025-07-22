# api/middleware.py - Cross-cutting Concerns
"""
Request/response processing
- Authentication
- CORS policies
- Global error handling
- Logging setup
"""

import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.config import llm_config

logger = logging.getLogger(__name__)


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Simple API key authentication middleware"""
    
    # function to check if the api key is valid
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for public endpoints
        if request.url.path in ["/", "/ping"]:
            return await call_next(request)
        
        # Skip authentication if not required
        if not llm_config.require_api_key or not llm_config.api_key:
            return await call_next(request)
        
        # Extract API key from Authorization header
        auth_header = request.headers.get("Authorization", "")
        api_key = None
        
        if auth_header.startswith("Bearer "):
            api_key = auth_header[7:]  # Remove "Bearer " prefix
        
        # Validate against configured key
        if api_key != llm_config.api_key:
            return JSONResponse(
                status_code=401,
                content={"error": "Unauthorized", "message": "Invalid or missing API key"}
            )
        
        return await call_next(request)


def setup_middleware(app: FastAPI) -> None:
    """Setup essential middleware for the FastAPI app"""
    
    # API key authentication middleware (if enabled)
    if llm_config.require_api_key:
        app.add_middleware(APIKeyMiddleware)
    
    # CORS middleware - restrictive for closed environments
    app.add_middleware(
        CORSMiddleware,
        allow_origins=llm_config.allowed_origins,   # list of allowed origins
        allow_credentials=True,                     # enables cookies/auth headers in CORS requests
        allow_methods=["GET", "POST", "OPTIONS"],   # allowed HTTP methods
        allow_headers=["Content-Type", "Authorization", "X-Client-ID"],  # allowed headers
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """Setup basic error handling"""
    
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        return JSONResponse(
            status_code=404,
            content={"error": "Not Found", "message": f"Endpoint {request.url.path} not found"}
        )
    
    @app.exception_handler(500)
    async def internal_error_handler(request: Request, exc):
        logger.error(f"Internal error: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal Server Error", "message": "Something went wrong"}
        )


def setup_logging():
    """Setup basic logging"""
    logging.basicConfig(
        level=getattr(logging, llm_config.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    
    # Reduce noise from external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO) 