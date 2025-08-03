"""
Main FastAPI application entry point
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
from pathlib import Path

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import configuration and routes
from core.config import llm_config
from api.routes import create_routes
from api.middleware import setup_middleware

# Create FastAPI app
app = FastAPI(
    title="Unified LLM API",
    description="A unified API for LLM-powered applications",
    version="1.0.0"
)

# Setup middleware (CORS, error handling, etc.)
setup_middleware(app)

# Create API routes
create_routes(app)

# Basic health check endpoint
@app.get("/")
async def root():
    """Root endpoint for basic connectivity check"""
    return {"status": "ok", "message": "LLM API is running"}

@app.get("/ping")
async def ping():
    """Simple ping endpoint for health checks"""
    return {"ping": "pong"} 