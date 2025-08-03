# core/models.py - Data Structures
"""
Data models and request/response schemas for the API
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, date

# ===============================
# CHAT MODELS
# ===============================

class Message(BaseModel):
    """Unified message format"""
    role: Literal["system", "user", "assistant"]
    content: str

    @field_validator('content')
    @classmethod
    def content_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Message content cannot be empty')
        return v.strip()


class ChatRequest(BaseModel):
    """Main request model for chat conversations"""
    messages: List[Message]
    session_id: Optional[str] = None
    stream: bool = True
    
    # Optional model parameters
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    
    @field_validator('messages')
    @classmethod
    def messages_not_empty(cls, v):
        if not v:
            raise ValueError('Messages list cannot be empty')
        return v
    


# ===============================
# TASK EXTRACTION MODELS
# ===============================

class TaskItem(BaseModel):
    sender: Optional[str]
    sending_date: Optional[date]
    assigned_to: str
    title: str
    description: str
    due_date: Optional[date]

    @field_validator("sending_date", "due_date", pre=True)
    @classmethod
    def parse_date(cls, v):
        if v is None:
            return v
        try:
            return datetime.strptime(v, "%d/%m/%Y").date()
        except ValueError:
            raise ValueError(f"Could not parse {v} to DD/MM/YYYY format")


class TaskExtractionRequest(BaseModel):
    email_content: str
    
    
# Change this to be a list of TaskItem, not wrapped in a dict
TaskExtractionResponse = List[TaskItem]


# ===============================
# HEALTH CHECK MODELS
# ===============================

class HealthStatus(BaseModel):
    """Unified health status and metrics model"""
    # Health indicators
    status: Literal["healthy", "unhealthy"]
    vllm_healthy: bool
    
    # System metrics  
    active_sessions: int
    uptime: Optional[float] = None
    
    # vLLM metrics (optional)
    vllm_running_requests: Optional[int] = None
    vllm_waiting_requests: Optional[int] = None
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.now)


class APIError(BaseModel):
    """Standardized error response model"""
    error: str
    error_type: Literal["validation", "server", "vllm", "timeout"]
    retryable: bool = False
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now) 

