# main.py - Application Bootstrap
"""
Create and configure FastAPI application
- Import all components
- Setup middleware  
- Register routes
- Configure logging
- Start server
"""

import logging

from fastapi import FastAPI

from .core.config import llm_config
from .api.routes import create_routes
from .api.middleware import setup_middleware, setup_exception_handlers, setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


# Create FastAPI app
app = FastAPI(
    title="Unified LLM API",
    description="Self-hosted LLM API for secure, air-gapped environments",
    version="1.0.0",
    docs_url=None,          # Disable docs
    redoc_url=None,         # Disable redoc
    openapi_url=None,       # Disable OpenAPI schema
)

# Setup middleware and exception handlers
setup_middleware(app)
setup_exception_handlers(app)

# Add API routes
create_routes(app)


# Simple health endpoint for load balancers
@app.get("/ping", include_in_schema=False)
async def ping():
    """Simple ping endpoint for load balancer health checks"""
    return {"status": "ok", "message": "pong"}


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint with API information"""
    return {
        "name": app.title,
        "version": "1.0.0",
        "status": "running",
        "health": "/api/health",
    }


# Entry point for direct execution
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "llm-api.main:app",
        host=llm_config.host,
        port=llm_config.port,
        log_level=llm_config.log_level.lower(),
        reload=True,    # Development mode
        access_log=True
    ) 