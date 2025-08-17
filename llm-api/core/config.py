"""
Configuration settings and environment variables
"""
import os
from typing import Dict, Any, List

class LLMConfig:
    """Configuration settings for the LLM API"""
    
    def __init__(self):
        # Base URLs for services
        self.base_url: str = os.getenv("LLM_API_BASE_URL", "http://localhost")
        self.cloud_ip: str = os.getenv("LLM_API_CLOUD_IP", "195.142.145.66")  # The public IP of the cloud instance
        self.frontend_port: int = int(os.getenv("LLM_API_FRONTEND_PORT", "15554"))  # 3000 mapped port
        self.api_port: int = int(os.getenv("LLM_API_API_PORT", "15591"))  # 8090 mapped port
        self.vllm_port: int = int(os.getenv("LLM_API_VLLM_PORT", "8060"))  # vLLM server port

        # Server settings
        self.host: str = os.getenv("LLM_API_HOST", "0.0.0.0")
        self.port: int = int(os.getenv("LLM_API_PORT", "8090"))
        self.log_level: str = os.getenv("LLM_API_LOG_LEVEL", "INFO")
        
        # Model Configuration
        self.llm_model_name: str = os.getenv("LLM_API_LLM_MODEL_NAME", "gaunernst/gemma-3-12b-it-qat-autoawq")
        
        # Model Parameters
        self.max_tokens: int = int(os.getenv("LLM_API_MAX_TOKENS", "2048"))
        self.temperature: float = float(os.getenv("LLM_API_TEMPERATURE", "0.7"))
        self.top_p: float = float(os.getenv("LLM_API_TOP_P", "0.9"))
        
        # Connection Settings
        self.request_timeout: int = int(os.getenv("LLM_API_REQUEST_TIMEOUT", "300"))
        self.health_check_timeout: int = int(os.getenv("LLM_API_HEALTH_CHECK_TIMEOUT", "5"))
        self.connection_pool_size: int = int(os.getenv("LLM_API_CONNECTION_POOL_SIZE", "100"))
        self.max_keepalive_connections: int = int(os.getenv("LLM_API_MAX_KEEPALIVE_CONNECTIONS", "50"))
        self.keepalive_expiry: float = float(os.getenv("LLM_API_KEEPALIVE_EXPIRY", "60.0"))

    @property
    def frontend_url(self) -> str:
        """Get frontend URL"""
        if self.base_url.endswith("/"):
            base = self.base_url[:-1]
        else:
            base = self.base_url
        return f"{base}:{self.frontend_port}"

    @property
    def api_url(self) -> str:
        """Get API URL"""
        if self.base_url.endswith("/"):
            base = self.base_url[:-1]
        else:
            base = self.base_url
        return f"{base}:{self.api_port}"
    
    @property
    def cloud_frontend_url(self) -> str:
        """Get cloud frontend URL"""
        return f"http://{self.cloud_ip}:{self.frontend_port}"
    
    @property
    def cloud_api_url(self) -> str:
        """Get cloud API URL"""
        return f"http://{self.cloud_ip}:{self.api_port}"

    @property
    def vllm_url(self) -> str:
        """Get vLLM base URL"""
        if self.base_url.endswith("/"):
            base = self.base_url[:-1]
        else:
            base = self.base_url
        return f"{base}:{self.vllm_port}"

    @property
    def vllm_api_url(self) -> str:
        """Get vLLM API endpoint"""
        return f"{self.vllm_url}/v1/chat/completions"

    @property
    def vllm_metrics_url(self) -> str:
        """Get vLLM metrics endpoint"""
        return f"{self.vllm_url}/metrics"

    @property
    def vllm_headers(self) -> Dict[str, str]:
        """Get headers for vLLM API requests"""
        return {"Content-Type": "application/json"}

    @property
    def allowed_origins(self) -> List[str]:
        """Get allowed CORS origins"""
        return [
            self.frontend_url,
            self.api_url,
            self.cloud_frontend_url,
            self.cloud_api_url,
        ]

    def get_model_params(self) -> Dict[str, Any]:
        """Get model parameters for API requests"""
        return {
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
        }


# Create global config instance
llm_config = LLMConfig() 