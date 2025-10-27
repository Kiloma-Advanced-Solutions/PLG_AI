"""
Data models for the application
"""
from pydantic import BaseModel

class Message(BaseModel):
    """Chat message model"""
    role: str  # "system", "user", or "assistant"
    content: str

