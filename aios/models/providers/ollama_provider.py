"""Ollama model provider for AIOS platform."""

import json
import os
from typing import List, Dict, Any, Optional
import urllib.request
import urllib.error

from ..base import BaseModel, Message
from ...core.exceptions import ModelProviderError


class OllamaProvider(BaseModel):
    """Ollama model provider for local LLMs."""

    def __init__(self, name: str, base_url: Optional[str] = None, **kwargs):
        """
        Initialize the Ollama provider.

        Args:
            name: Name of the model (e.g., 'llama3.2:3b').
            base_url: Base URL for Ollama API. If None, will try to get from
                     environment variable OLLAMA_BASE_URL, then default to
                     http://localhost:11434.
            **kwargs: Additional model-specific parameters.
        """
        super().__init__(name, **kwargs)

        # Determine base URL: parameter > environment variable > default
        if base_url is not None:
            self.base_url = base_url.rstrip('/')
        else:
            self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip('/')

        self.call_count = 0

    def generate(self, messages: List[Message], **kwargs) -> str:
        """
        Generate a response from Ollama model.

        Args:
            messages: List of conversation messages.
            **kwargs: Additional generation parameters (temperature, top_p, etc.).
                     These will be passed in the 'options' field of the Ollama API.

        Returns:
            str: Generated response text.

        Raises:
            ModelProviderError: If there's an error communicating with Ollama.
        """
        self.call_count += 1

        # Convert Message objects to Ollama format
        ollama_messages = [{"role": msg.role, "content": msg.content} for msg in messages]
        
        # Prepare the request payload
        payload = {
            "model": self.name,
            "messages": ollama_messages,
            "stream": False,
        }

        # Add additional parameters to options if any
        if kwargs:
            payload["options"] = kwargs

        # Prepare the request
        url = f"{self.base_url}/api/chat"
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        try:
            with urllib.request.urlopen(req) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                
                # Extract the message content
                if "message" not in response_data:
                    raise ModelProviderError("Invalid response from Ollama: missing 'message' field")
                
                message = response_data["message"]
                if "content" not in message:
                    raise ModelProviderError("Invalid response format from Ollama")
                
                return message["content"].strip()
                
        except urllib.error.HTTPError as e:
            # Try to read error response body
            error_msg = f"Ollama API error: {e.code} {e.reason}"
            try:
                error_body = e.read().decode('utf-8')
                error_data = json.loads(error_body)
                if "error" in error_data:
                    error_msg += f": {error_data['error']}"
            except Exception:
                pass  # If we can't parse error body, just use the HTTP error info
            raise ModelProviderError(error_msg)
        except urllib.error.URLError as e:
            raise ModelProviderError(f"Failed to connect to Ollama: {e.reason}")
        except json.JSONDecodeError as e:
            raise ModelProviderError(f"Invalid JSON response from Ollama: {str(e)}")
        except Exception as e:
            if isinstance(e, ModelProviderError):
                raise
            raise ModelProviderError(f"Unexpected error when communicating with Ollama: {str(e)}")

    def is_available(self) -> bool:
        """
        Check if the Ollama model is available by checking if the model exists
        in the local Ollama instance.

        Returns:
            bool: True if model is available, False otherwise.
        """
        try:
            url = f"{self.base_url}/api/tags"
            with urllib.request.urlopen(url) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                
                # Check if our model is in the list
                if "models" in response_data:
                    model_names = [model.get("name") for model in response_data["models"]]
                    return self.name in model_names
                return False
        except Exception:
            return False

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the Ollama model.

        Returns:
            Dict[str, Any]: Model information.
        """
        info = super().get_info()
        info.update({
            "call_count": self.call_count,
            "type": "OllamaProvider",
            "base_url": self.base_url
        })
        return info
