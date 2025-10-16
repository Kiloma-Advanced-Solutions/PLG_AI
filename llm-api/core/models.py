# core/models.py - Data Structures
"""
Data models and request/response schemas for the API
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, field_validator, EmailStr
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
    
    # MCP integration (optional)
    use_mcp: Optional[bool] = True  # Enable MCP tools by default
    
    @field_validator('messages')
    @classmethod
    def messages_not_empty(cls, v):
        if not v:
            raise ValueError('Messages list cannot be empty')
        return v
    


# ===============================
# TITLE GENERATION MODELS
# ===============================

class TitleGenerationRequest(BaseModel):
    """Request for generating a conversation title"""
    user_message: str


class TitleGenerationResponse(BaseModel):
    """Response containing a 6-word title"""
    title: str



    
# ===============================
# TASK EXTRACTION MODELS
# ===============================

class TaskItem(BaseModel):
    sender: Optional[str] = None
    sending_date: Optional[date] = None
    assigned_to: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None


class TaskExtractionRequest(BaseModel):
    email_content: str
    
    
# List of TaskItems
TaskExtractionResponse = List[TaskItem]



# ===============================
# EMAIL SUMMARIZATION MODELS
# ===============================

class EmailSummary(BaseModel):
    sender: Optional[EmailStr] = None
    sending_date: Optional[datetime] = None
    title: Optional[str] = None
    summary: Optional[str] = None


class EmailSummarizationRequest(BaseModel):
    email_content: str
    length: int = 100


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

