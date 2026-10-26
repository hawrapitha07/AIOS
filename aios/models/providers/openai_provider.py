"""
OpenAI model provider for AIOS platform.
"""

import os
import time
from typing import List, Dict, Any, Optional
from ..base import BaseModel, Message

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class OpenAIProvider(BaseModel):
    """OpenAI model provider."""

    def __init__(self, name: str, api_key: Optional[str] = None, **kwargs):
        """
        Initialize the OpenAI provider.

        Args:
            name: Name of the model (e.g., 'gpt-4o-mini').
            api_key: OpenAI API key. If None, will try to get from environment.
            **kwargs: Additional model-specific parameters.
        """
        super().__init__(name, **kwargs)

        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not installed. Install with: pip install openai")

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")

        self.client = openai.OpenAI(api_key=self.api_key)
        self.call_count = 0

    def generate(self, messages: List[Message], **kwargs) -> str:
        """
        Generate a response from OpenAI model.

        Args:
            messages: List of conversation messages.
            **kwargs: Additional generation parameters (temperature, max_tokens, etc.).

        Returns:
            str: Generated response text.
        """
        self.call_count += 1

        # Convert Message objects to OpenAI format
        openai_messages = [msg.to_dict() for msg in messages]

        # Set default parameters
        params = {
            "model": self.name,
            "messages": openai_messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 150),
        }

        # Add any additional parameters
        for key, value in kwargs.items():
            if key not in ["temperature", "max_tokens"]:
                params[key] = value

        try:
            response = self.client.chat.completions.create(**params)
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

    def is_available(self) -> bool:
        """
        Check if the OpenAI model is available by attempting a simple API call.

        Returns:
            bool: True if model is available, False otherwise.
        """
        if not self.api_key:
            return False

        try:
            # Make a minimal API call to check availability
            self.client.models.list()
            return True
        except Exception:
            return False

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the OpenAI model.

        Returns:
            Dict[str, Any]: Model information.
        """
        info = super().get_info()
        info.update({
            "call_count": self.call_count,
            "type": "OpenAIProvider",
            "api_key_configured": bool(self.api_key)
        })
        return info