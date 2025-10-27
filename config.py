"""
Configuration for the application
"""
import os
from dotenv import load_dotenv

load_dotenv()

class LLMConfig:
    """Configuration for LLM services"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.llm_model_name = "gpt-3.5-turbo"
        # Support multiple MCP servers
        mcp_servers_str = os.getenv("MCP_SERVERS", "http://localhost:8000,http://localhost:8002")
        self.mcp_servers = [url.strip() for url in mcp_servers_str.split(",")]
        self.request_timeout = 60
        self.max_keepalive_connections = 5
        self.connection_pool_size = 10
        self.keepalive_expiry = 30
        
    def get_model_params(self):
        """Get model-specific parameters"""
        return {
            "temperature": 0.7,
            "max_tokens": 1000,
        }

# Global config instance
llm_config = LLMConfig()

