import sys

# The content we want to write to agent.py
content = '''from aios.models.base import Message
from aios.managers.model_manager import ModelManager
from aios.developer.intent import DeveloperIntent, DeveloperAction
from aios.developer.prompts import SYSTEM_PROMPT
from aios.developer.operations import DeveloperOperationExecutor
from aios.core.exceptions import AIOSException
import json
import re


class DeveloperAgent:
    def __init__(self):
        self.model_manager = ModelManager()
        self.operation_executor = DeveloperOperationExecutor()

    def _get_model(self):
        # Use the project's configured model
        from aios.core.config import load_config
        config = load_config()
        # If the model provider is not available, we might want to fall back to mock?
        # For simplicity, we'll just try to get the model.
        # If it fails, we'll raise an exception.
        try:
            model = self.model_manager.create_model(
                provider=config.model.provider,
                name=config.model.name
            )
        except Exception:
            # Fall back to mock model for the developer agent if the configured model is not available
            model = self.model_manager.create_model(
                provider='mock',
                name='default'
            )
        return model

    def _clean_json_response(self, response: str) -> str:
        # Try to extract JSON from the response
        # Look for the first '{' and the last '}'
        start = response.find('{')
        end = response.rfind('}')
        if start != -1 and end != -1 and start < end:
            json_str = response[start:end+1]
            # Try to see if it's valid JSON by attempting to parse it
            try:
                json.loads(json_str)
                return json_str
            except json.JSONDecodeError:
                pass
        # If we can't find a valid JSON, return the original response
        return response

    def process_request(self, user_request: str) -> DeveloperIntent:
        # Get the model to use for the developer agent
        model = self._get_model()

        # Prepare the messages for the model
        messages = [
            Message(role="system", content=SYSTEM_PROMPT),
            Message(role="user", content=user_request)
        ]

        # Generate a response from the model
        try:
            response = model.generate(messages)
        except Exception as e:
            raise AIOSException(f"Failed to generate response from model: {e}")

        # Clean the response to extract JSON
        cleaned_response = self._clean_json_response(response)

        # Parse the JSON
        try:
            intent_dict = json.loads(cleaned_response)
        except json.JSONDecodeError:
            raise AIOSException(f"Could not parse JSON from model response. Response: {response}")

        # Validate the intent using the DeveloperIntent model
        try:
            intent = DeveloperIntent(**intent_dict)
        except Exception as e:
            raise AIOSException(f"Invalid intent: {e}")

        return intent

    def execute_request(self, user_request: str) -> str:
        # Process the request to get the intent
        intent = self.process_request(user_request)

        # Execute the operation
        try:
            result = self.operation_executor.execute(intent)
        except Exception as e:
            raise AIOSException(f"Failed to execute operation: {e}")

        return result
'''
# Write the file
with open('aios/developer/agent.py', 'w') as f:
    f.write(content)
