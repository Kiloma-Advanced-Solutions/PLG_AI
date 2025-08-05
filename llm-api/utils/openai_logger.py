"""
Simple OpenAI API Request Logger

Automatically logs all OpenAI API REQUESTS to files (responses are not logged).
Just replace `openai.OpenAI()` with `OpenAILogger()` - that's it!

Environment Variables:
    OPENAI_LOGGING_ENABLED: Set to "false" to disable logging (default: true)
    OPENAI_LOG_DIR: Directory for log files (default: tests/logs/openai_requests)
"""
import json
import os
from datetime import datetime
from typing import Any, Optional
import openai


class OpenAILogger:
    """
    Drop-in replacement for openai.OpenAI that automatically logs all REQUESTS (not responses)
    
    Usage:
        # Instead of: client = openai.OpenAI(api_key=api_key)
        # Use: client = OpenAILogger(api_key=api_key)
    """
    
    def __init__(self, api_key: str, log_dir: str = None, **kwargs):
        # Create the actual OpenAI client
        self._client = openai.OpenAI(api_key=api_key, **kwargs)
        
        # Check if logging is enabled via environment variable
        logging_enabled = os.getenv('OPENAI_LOGGING_ENABLED', 'true').lower() != 'false'
        
        # Set up logging directory
        if log_dir is None:
            log_dir = os.getenv('OPENAI_LOG_DIR', 'tests/logs/openai_requests')
        
        self.log_dir = log_dir
        self.logging_enabled = logging_enabled
        
        if logging_enabled:
            os.makedirs(log_dir, exist_ok=True)
            # Wrap the chat completions to add logging
            self.chat = ChatCompletionsWrapper(self._client.chat, self.log_dir)
        else:
            # No logging - just pass through to regular client
            self.chat = self._client.chat
    
    def __getattr__(self, name):
        """Pass through any other attributes to the real client"""
        return getattr(self._client, name)


class ChatCompletionsWrapper:
    """Wraps chat.completions to add logging"""
    
    def __init__(self, chat_client, log_dir: str):
        self._chat = chat_client
        self.log_dir = log_dir
        self.completions = CompletionsWrapper(chat_client.completions, log_dir)


class CompletionsWrapper:
    """Wraps chat.completions.create to add request logging (responses not logged)"""
    
    def __init__(self, completions_client, log_dir: str):
        self._completions = completions_client
        self.log_dir = log_dir
    
    def create(self, **kwargs):
        """Log only the request data"""
        # Generate unique ID for this request
        timestamp = datetime.now()
        request_id = timestamp.strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
        
        # Log only the request
        request_data = {
            "timestamp": timestamp.isoformat(),
            "request_id": request_id,
            "method": "chat.completions.create",
            "parameters": kwargs
        }
        
        request_file = os.path.join(self.log_dir, f"request_{request_id}.json")
        
        try:
            # Save request
            with open(request_file, 'w', encoding='utf-8') as f:
                json.dump(request_data, f, indent=2, ensure_ascii=False, default=str)
        except Exception:
            # If logging fails, just continue silently
            pass
        
        # Make the actual API call (no response logging)
        return self._completions.create(**kwargs)
    
    def __getattr__(self, name):
        """Pass through any other methods"""
        return getattr(self._completions, name)