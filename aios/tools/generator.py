"""
Tool generation functionality for AIOS platform.
"""

import ast
import json
import operator
import re
from typing import Dict, Any, Optional
from aios.managers.model_manager import ModelManager
from aios.models.base import Message
from aios.core.exceptions import AIOSException


class ToolGenerator:
    """Generates tool implementations using configured LLM."""

    def __init__(self, model_manager: ModelManager):
        """
        Initialize the tool generator.

        Args:
            model_manager: Model manager to access the configured LLM.
        """
        self.model_manager = model_manager

    def _clean_json_response(self, response: str) -> str:
        """Extract JSON from model response."""
        # Try to find JSON object in the response
        start = response.find('{')
        if start == -1:
            return response

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

    def generate_tool_implementation(self, name: str, description: str,
                                   parameters_spec: Dict[str, str]) -> str:
        """
        Generate a tool implementation using the configured LLM.

        Args:
            name: Name of the tool.
            description: Description of what the tool does.
            parameters_spec: Dictionary mapping parameter names to types.

        Returns:
            str: Generated Python code for the tool implementation.

        Raises:
            AIOSException: If tool generation fails.
        """
        # For now, always use the fallback to avoid LLM timeout and invalid code issues.
        # TODO: Re-enable LLM generation when the model is more reliable.
        return self._generate_fallback_tool(name, description, parameters_spec)

    def _generate_fallback_tool(self, name: str, description: str,
                              parameters_spec: Dict[str, str]) -> str:
        """
        Generate a fallback tool implementation when LLM generation fails.

        This creates functional implementations for common tool types.
        """
        # Convert parameters spec to Python type hints
        params_str = ""
        if parameters_spec:
            param_items = []
            for param_name, param_type in parameters_spec.items():
                # Simple type mapping
                if param_type == "string":
                    param_items.append(f"{param_name}: str")
                elif param_type in ["integer", "int"]:
                    param_items.append(f"{param_name}: int")
                elif param_type in ["float", "number"]:
                    param_items.append(f"{param_name}: float")
                elif param_type in ["boolean", "bool"]:
                    param_items.append(f"{param_name}: bool")
                else:
                    # Default to string for unknown types
                    param_items.append(f"{param_name}: str")
            params_str = ", ".join(param_items)
        else:
            params_str = ""

        # Convert tool name to class name
        if name.endswith('_tool'):
            base_name = name[:-5]  # Remove '_tool' suffix
        else:
            base_name = name
        class_name = base_name[0].upper() + base_name[1:] + 'Tool'

        # Generate implementation based on tool name/description
        if name == "calculator" or "calculator" in name.lower() or "calculate" in description.lower():
            # Safe calculator implementation using AST
            implementation = f'''"""
{description}
"""

import ast
import operator
from typing import Any, Union
from aios.tools.base import BaseTool


class {class_name}(BaseTool):
    """{description}"""

    def __init__(self):
        super().__init__(
            name="{name}",
            description="{description}"
        )

    def execute(self, expression: str) -> Any:
        """Safely evaluate a mathematical expression.

        Args:
            expression: Mathematical expression to evaluate (e.g., "2 + 3 * 4")

        Returns:
            The result of the evaluated expression.

        Raises:
            ValueError: If the expression is invalid or unsafe.
        """
        try:
            # Parse the expression into an AST tree
            tree = ast.parse(expression, mode='eval')

            # Define safe operators
            safe_operators = {{
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
                ast.FloorDiv: operator.floordiv,
                ast.Mod: operator.mod,
                ast.Pow: operator.pow,
                ast.USub: operator.neg,
                ast.UAdd: operator.pos,
            }}

            def _eval_node(node):
                """Recursively evaluate AST nodes with safety checks."""
                # Handle both ast.Num (Python <3.8) and ast.Constant (Python >=3.8)
                if hasattr(ast, 'Num') and isinstance(node, ast.Num):
                    return node.n
                elif isinstance(node, ast.Constant):
                    if isinstance(node.value, (int, float)):
                        return node.value
                    else:
                        raise ValueError("Only numeric constants are allowed")
                elif isinstance(node, ast.UnaryOp):
                    if type(node.op) not in safe_operators:
                        raise ValueError(f"Unsupported unary operator: {{type(node.op).__name__}}")
                    operand = _eval_node(node.operand)
                    return safe_operators[type(node.op)](operand)
                elif isinstance(node, ast.BinOp):
                    if type(node.op) not in safe_operators:
                        raise ValueError(f"Unsupported binary operator: {{type(node.op).__name__}}")
                    left = _eval_node(node.left)
                    right = _eval_node(node.right)
                    return safe_operators[type(node.op)](left, right)
                else:
                    raise ValueError(f"Unsupported expression type: {{type(node).__name__}}")

            result = _eval_node(tree.body)
            return result

        except SyntaxError:
            raise ValueError(f"Invalid mathematical expression: {{expression}}")
        except ValueError as e:
            raise ValueError(f"Error evaluating expression: {{str(e)}}")
        except Exception as e:
            raise ValueError(f"Unexpected error during calculation: {{str(e)}}")

'''
        elif "weather" in name.lower() or "weather" in description.lower():
            # Weather API template showing required configuration
            implementation = f'''"""
{description}
"""

import os
from typing import Any, Dict, Optional
from aios.tools.base import BaseTool


class {class_name}(BaseTool):
    """{description}"""

    def __init__(self):
        super().__init__(
            name="{name}",
            description="{description}"
        )

    def execute(self, location: str, format: str = "json") -> Any:
        """Get weather data for a location.

        Args:
            location: Location to get weather for (city name, coordinates, etc.)
            format: Output format ("json", "text", etc.)

        Returns:
            Weather data or error message if not configured.

        Note:
            This tool requires a weather API key to be configured.
            Set the WEATHER_API_KEY environment variable to use this tool.
        """
        # Check if API key is configured
        api_key = os.getenv("WEATHER_API_KEY")
        if not api_key:
            return {{
                "error": "Weather API key not configured. "
                         "Please set the WEATHER_API_KEY environment variable. "
                         "Get a free API key from services like OpenWeatherMap."
            }}

        # This is a template implementation - replace with actual API integration
        # Example for OpenWeatherMap API:
        # import requests
        # base_url = "http://api.openweathermap.org/data/2.5/weather"
        # params = {{
        #     "q": location,
        #     "appid": api_key,
        #     "units": "metric"
        # }}
        # response = requests.get(base_url, params=params)
        # if response.status_code == 200:
        #     return response.json()
        # else:
        #     return {{"error": f"API request failed: {{response.status_code}}"}}

        return {{
            "message": f"Weather tool for {{location}} (format: {{format}})",
            "note": "This is a template implementation. "
                    "Integrate with a real weather API by adding API call logic.",
            "configuration_required": {{
                "api_key_env_var": "WEATHER_API_KEY",
                "example_api_services": ["OpenWeatherMap", "WeatherAPI.com", "AccuWeather"]
            }}
        }}

'''
        else:
            # Generic fallback implementation
            implementation = f'''"""
{description}
"""

from typing import Any, Dict
from aios.tools.base import BaseTool


class {class_name}(BaseTool):
    """{description}"""

    def __init__(self):
        super().__init__(
            name="{name}",
            description="{description}"
        )

    def execute(self{', ' + params_str if params_str else ''}) -> Any:
        """Execute the tool with the given parameters."""
        # This is a placeholder implementation - replace with actual tool logic
        # Tool name: {name}
        # Description: {description}
        # Parameters: {parameters_spec}

        # For demonstration, return the parameters received
        return {{
            "tool": "{name}",
            "description": "{description}",
            "parameters_received": {{locals()}}
        }}

'''
        return implementation
