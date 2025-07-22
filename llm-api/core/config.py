# core/config.py - Configuration Management
"""
All configurations
- Environment variables
- Default settings
- Validation rules
- System prompts
"""

import os
from typing import Dict, Any, Optional, List
from pydantic import BaseSettings, validator


class LLMConfig(BaseSettings):
    """Main configuration for the LLM API with environment variable support"""
    
    # vLLM Server Configuration
    vllm_base_url: str = "http://localhost:8000"
    vllm_api_url: str = "http://localhost:8000/v1/chat/completions"
    vllm_metrics_url: str = "http://localhost:8000/metrics"
    model_name: str = "gaunernst/gemma-3-12b-it-qat-autoawq"
    
    # API Server Configuration
    host: str = "0.0.0.0"
    port: int = 8090
    
    # CORS Configuration - More secure defaults
    allowed_origins: List[str] = [
        "http://localhost:3000",      # Next.js development
        "http://localhost:8090",      # API development
    ]
    
    # Chat Model Parameters
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9
    
    # Timeouts and Connection Configuration
    request_timeout: int = 300           # Extended timeout for long generations
    health_check_timeout: int = 5
    connection_pool_size: int = 100      # HTTP connection pool to vLLM
    max_keepalive_connections: int = 50  # Keep-alive connections to vLLM
    keepalive_expiry: float = 60.0       # Seconds to keep connections alive
    
    # Logging Configuration
    log_level: str = "INFO"
    
    # Security Configuration
    api_key: Optional[str] = None  # Set via LLM_API_API_KEY environment variable
    require_api_key: bool = False  # Set to True for production

    @validator('allowed_origins')
    def validate_origins(cls, v):
        if not v:  # Don't allow empty list
            raise ValueError("At least one origin must be specified")
        return v

    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {', '.join(valid_levels)}")
        return v.upper()

    @validator('temperature')
    def validate_temperature(cls, v):
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v

    @validator('top_p')
    def validate_top_p(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Top-p must be between 0.0 and 1.0")
        return v

    class Config:
        env_file = ".env"
        env_prefix = "LLM_API_"
        case_sensitive = False


# System prompts for different use cases (examples - should be passed dynamically)
DEFAULT_SYSTEM_PROMPTS = {
    "chat": """אתה עוזר בינה מלאכותית שמטרתו לספק מידע מדויק ואמין בשפה העברית. ענה באופן ברור, מדויק, ומבוסס על עובדות בלבד. אל תנחש – אם אינך בטוח בתשובה, כתוב שאתה לא יודע או שהמידע חסר.""",
    
    "email": """אתה עוזר בינה מלאכותית המתמחה בניתוח וסיכום הודעות דואר אלקטרוני בעברית. ספק סיכומים קצרים וברורים של התוכן העיקרי, זהה נושאים חשובים ופעולות נדרשות.""",
    
    "task": """אתה עוזר בינה מלאכותית המתמחה בחילוץ משימות ופעולות נדרשות מטקסטים בעברית. זהה ורשום בצורה מובנית את כל המשימות, התאריכים החשובים והפעולות הנדרשות."""
}


# Global configuration instance
llm_config = LLMConfig()


def get_default_system_prompt(use_case: str = "chat") -> str:
    """
    Get default system prompt for the specified use_case
    
    Args:
        use_case: use_case variant (chat/email/task)
    
    Returns:
        Default system prompt string
    """
    return DEFAULT_SYSTEM_PROMPTS.get(use_case, DEFAULT_SYSTEM_PROMPTS["chat"])


def get_model_params() -> Dict[str, Any]:
    """
    Get model parameters for chat completions
    
    Returns:
        Dictionary of model parameters ready for vLLM API
    """
    return {
        "model": llm_config.model_name,
        "max_tokens": llm_config.max_tokens,
        "temperature": llm_config.temperature,
        "top_p": llm_config.top_p,
    } 