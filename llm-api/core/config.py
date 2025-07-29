"""
Configuration management for the LLM API
"""
from typing import Dict, Any, List
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings

class LLMConfig(BaseSettings):
    """Configuration settings for the LLM API"""
    
    # Base URLs for services
    base_url: str = Field(
        default="http://localhost",
        description="Base URL for all services"
    )
    frontend_port: int = Field(
        default=40959,  # 3000 mapped port
        description="Frontend port"
    )
    api_port: int = Field(
        default=40908,  # 8090 mapped port
        description="API port"
    )
    vllm_port: int = Field(
        default=8000,  # vLLM server port
        description="vLLM server port"
    )

    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8090
    log_level: str = "INFO"
    
    # Model Configuration
    llm_model_name: str = "gaunernst/gemma-3-12b-it-qat-autoawq"
    
    # Model Parameters
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9
    
    # Connection Settings
    request_timeout: int = 300
    health_check_timeout: int = 5
    connection_pool_size: int = 100
    max_keepalive_connections: int = 50
    keepalive_expiry: float = 60.0

    @computed_field
    @property
    def frontend_url(self) -> str:
        """Get frontend URL"""
        if self.base_url.endswith("/"):
            base = self.base_url[:-1]
        else:
            base = self.base_url
        return f"{base}:{self.frontend_port}"

    @computed_field
    @property
    def api_url(self) -> str:
        """Get API URL"""
        if self.base_url.endswith("/"):
            base = self.base_url[:-1]
        else:
            base = self.base_url
        return f"{base}:{self.api_port}"

    @computed_field
    @property
    def vllm_url(self) -> str:
        """Get vLLM base URL"""
        if self.base_url.endswith("/"):
            base = self.base_url[:-1]
        else:
            base = self.base_url
        return f"{base}:{self.vllm_port}"

    @computed_field
    @property
    def vllm_api_url(self) -> str:
        """Get vLLM API endpoint"""
        return f"{self.vllm_url}/v1/chat/completions"

    @computed_field
    @property
    def vllm_metrics_url(self) -> str:
        """Get vLLM metrics endpoint"""
        return f"{self.vllm_url}/metrics"

    @computed_field
    @property
    def vllm_headers(self) -> Dict[str, str]:
        """Get headers for vLLM API requests"""
        return {"Content-Type": "application/json"}

    @computed_field
    @property
    def allowed_origins(self) -> List[str]:
        """Get allowed CORS origins"""
        return [
            self.frontend_url,
            self.api_url,
            "http://localhost:3000",  # Local development
            "http://localhost:8090",   # Local API
            "http://211.72.13.201:40959",  # Cloud frontend URL
            "http://211.72.13.201:40908",  # Cloud API URL
        ]

    class Config:
        env_prefix = "LLM_API_"


# Create global config instance
llm_config = LLMConfig()


def get_model_params() -> Dict[str, Any]:
    """Get model parameters for API requests"""
    return {
        "max_tokens": llm_config.max_tokens,
        "temperature": llm_config.temperature,
        "top_p": llm_config.top_p,
    } 