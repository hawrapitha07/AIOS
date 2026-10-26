"""
Mock model provider for AIOS platform.
Provides deterministic responses for testing and development.
"""

import json
import time
from typing import List, Dict, Any, Optional
from ..base import BaseModel, Message


class MockModel(BaseModel):
    """Mock model that provides deterministic responses."""

    def __init__(self, name: str = "default", **kwargs):
        """
        Initialize the mock model.

        Args:
            name: Name of the model.
            **kwargs: Additional model-specific parameters.
        """
        super().__init__(name, **kwargs)
        self.call_count = 0
        self.last_messages: List[Message] = []

    def generate(self, messages: List[Message], **kwargs) -> str:
        """
        Generate a mock response based on the input messages.

        Args:
            messages: List of conversation messages.
            **kwargs: Additional generation parameters.

        Returns:
            str: Mock response text.
        """
        self.call_count += 1
        self.last_messages = messages.copy()

        # Check if this is a request from the AIOS Developer Agent
        is_developer_agent = False
        for msg in messages:
            if msg.role == "system" and "You are the AIOS Developer Agent." in msg.content:
                is_developer_agent = True
                break

        if is_developer_agent:
            # Get the last user message
            last_user_message = ""
            for msg in reversed(messages):
                if msg.role == "user":
                    last_user_message = msg.content
                    break

            last_user_message_lower = last_user_message.lower()

            # Check for clarification requests
            if any(phrase in last_user_message_lower for phrase in [
                "switch to a local llm",
                "use a local model",
                "switch to local",
                "use local model",
                "local llm",
                "local model"
            ]):
                return json.dumps({
                    "action": "clarification_required",
                    "parameters": {
                        "question": "Which local model do you want to use?"
                    }
                })

            # Check for API model clarification
            if any(phrase in last_user_message_lower for phrase in [
                "switch to an api model",
                "use an api model",
                "switch to api",
                "use api model",
                "switch to an api llm",
                "use an api llm"
            ]):
                return json.dumps({
                    "action": "clarification_required",
                    "parameters": {
                        "question": "Which API provider do you want to use?"
                    }
                })

            # Check for tool creation requests
            if "create a tool" in last_user_message_lower or "create a" in last_user_message_lower:
                # Try to extract tool name and description
                # For simplicity, we'll look for common tool names
                if "calculator" in last_user_message_lower:
                    tool_name = "calculator"
                    tool_description = "Performs arithmetic calculations"
                    tool_parameters_spec = {"expression": "string"}
                elif "weather" in last_user_message_lower:
                    tool_name = "weather"
                    tool_description = "Get weather data for a location"
                    tool_parameters_spec = {"location": "string", "format": "string"}
                else:
                    # Default to a test tool
                    tool_name = "test_tool"
                    tool_description = "A test tool"
                    tool_parameters_spec = {"input": "string"}

                return json.dumps({
                    "action": "create_tool",
                    "parameters": {
                        "name": tool_name,
                        "description": tool_description,
                        "parameters_spec": tool_parameters_spec
                    }
                })

            # Check for setting model provider
            if "set model provider to" in last_user_message_lower:
                # Extract the provider name
                parts = last_user_message_lower.split("set model provider to")
                if len(parts) > 1:
                    provider = parts[1].strip()
                    # Remove any trailing punctuation or extra words
                    provider = provider.split()[0] if provider.split() else ""
                    if provider in ["ollama", "openai", "mock"]:
                        return json.dumps({
                            "action": "set_model_provider",
                            "parameters": {
                                "provider": provider
                            }
                        })

            # Check for setting model name
            if "set model to" in last_user_message_lower:
                parts = last_user_message_lower.split("set model to")
                if len(parts) > 1:
                    model_name = parts[1].strip()
                    # Take the first word as the model name for simplicity
                    model_name = model_name.split()[0] if model_name.split() else ""
                    if model_name:
                        return json.dumps({
                            "action": "set_model",
                            "parameters": {
                                "name": model_name
                            }
                        })

            # If we don't match any known pattern, return a default response
            # For now, we'll return a show_status action
            return json.dumps({
                "action": "show_status",
                "parameters": {}
            })

        # If not the developer agent, use the original mock behavior
        # Create a simple deterministic response based on the last user message
        last_user_message = ""
        for msg in reversed(messages):
            if msg.role == "user":
                last_user_message = msg.content
                break

        if not last_user_message:
            last_user_message = "(no user message)"

        # Generate a simple mock response
        response = f"Mock response #{self.call_count} to: '{last_user_message[:50]}...'"

        # Add some variation based on parameters
        temperature = kwargs.get("temperature", 0.7)
        if temperature > 0.8:
            response += " (creative mode)"
        elif temperature < 0.3:
            response += " (focused mode)"

        max_tokens = kwargs.get("max_tokens")
        if max_tokens:
            response += f" [limited to {max_tokens} tokens]"

        # Simulate processing time
        time.sleep(0.1)

        return response

    def is_available(self) -> bool:
        """
        Check if the mock model is available.

        Returns:
            bool: Always True for mock model.
        """
        return True

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the mock model.

        Returns:
            Dict[str, Any]: Model information.
        """
        info = super().get_info()
        info.update({
            "call_count": self.call_count,
            "type": "MockModel"
        })
        return info