"""Developer agent for AIOS platform."""

from aios.models.base import Message
from aios.managers.model_manager import ModelManager
from aios.developer.intent import DeveloperIntent, DeveloperAction
from aios.developer.prompts import SYSTEM_PROMPT
from aios.developer.operations import DeveloperOperationExecutor
from aios.core.exceptions import AIOSException
from aios.core.config import load_config, ModelConfig
import json
import re
import sys
import os
from pathlib import Path


class DeveloperAgent:
    def __init__(self):
        self.model_manager = ModelManager()
        self.operation_executor = DeveloperOperationExecutor()

    def _get_model(self):
        # Search for aios.yaml starting from current directory and going up
        current = Path.cwd()
        aios_yaml_path = None

        while True:
            candidate = current / "aios.yaml"

            if candidate.exists():
                aios_yaml_path = candidate
                break

            if current == current.parent:
                break

            current = current.parent

        if aios_yaml_path is None:
            raise AIOSException(
                "No AIOS project found (no aios.yaml in current directory or parent directories)."
            )

        config = load_config(str(aios_yaml_path))

    # Developer Agent always uses the developer model
    # when it is explicitly configured.
        provider = config.model.provider
        name = config.model.name

        try:
            model = self.model_manager.create_model(
                provider=provider,
                name=name
            )
        except Exception as e:
            raise AIOSException(
                f"Failed to initialize developer model '{name}' "
                f"with provider '{provider}': {e}"
            )

        return model

    def _clean_json_response(self, response: str) -> str:
        # Try to extract a valid JSON object from the response
        # Find the first '{'
        start = response.find('{')
        if start == -1:
            return response
        # Use a stack to find matching '}'
        brace_count = 0
        in_string = False
        escape_next = False
        for i in range(start, len(response)):
            ch = response[i]
            if escape_next:
                escape_next = False
                continue
            if ch == '\\':
                escape_next = True
                continue
            if ch == '"' and not escape_next:
                in_string = not in_string
                continue
            if not in_string:
                if ch == '{':
                    brace_count += 1
                elif ch == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        # Found matching closing brace
                        json_str = response[start:i+1]
                        # Try to parse it
                        try:
                            json.loads(json_str)
                            return json_str
                        except json.JSONDecodeError:
                            # If parsing fails, continue to look for another '}'
                            pass
        # If we couldn't find a valid JSON, return the original response
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

        # For clarification_required actions, extract question from parameters if needed
        if (intent_dict.get("action") == "clarification_required"
            and "parameters" in intent_dict
            and isinstance(intent_dict["parameters"], dict)
            and "question" in intent_dict["parameters"]
            and "question" not in intent_dict):
            # Move question from parameters to top level for DeveloperIntent compatibility
            intent_dict["question"] = intent_dict["parameters"]["question"]

        # Validate the intent using the DeveloperIntent model
        try:
            intent = DeveloperIntent(**intent_dict)
        except Exception as e:
            raise AIOSException(f"Invalid intent: {e}")

        return intent

    def execute_request(self, user_request: str) -> str:
        # Process the request to get the intent
        intent = self.process_request(user_request)

        # Handle clarification required
        if intent.action == DeveloperAction.CLARIFICATION_REQUIRED:
            # Return the clarification question to the user
            if intent.question:
                return intent.question
            else:
                return "I need more information to help you. Please clarify your request."

        # Execute the operation
        try:
            result = self.operation_executor.execute(intent)
        except Exception as e:
            raise AIOSException(f"Failed to execute operation: {e}")

        return result
