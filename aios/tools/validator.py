"""
Tool validation functionality for AIOS platform.
"""

import ast
import re
from typing import Any, List
from aios.tools.base import BaseTool
from aios.core.exceptions import AIOSException


class ToolValidator:
    """Validates generated tool implementations."""

    # Dangerous patterns to reject
    DANGEROUS_PATTERNS = [
        r'\beval\s*\(',
        r'\bexec\s*\(',
        r'\bcompile\s*\(',
        r'__import__\s*\(',
        r'\bopen\s*\([^)]*["\'](?:[^"]*["\']{2})',  # open with mode w/a/x
        r'\bos\.system\s*\(',
        r'\bos\.popen\s*\(',
        r'\bsubprocess\.',
        r'\bfilesystem\.',  # Generic filesystem access
        r'\bshutil\.(?:rmtree|move|copy)',  # Dangerous shutil operations
    ]

    def __init__(self):
        """Initialize the tool validator."""
        self.dangerous_regexes = [re.compile(pattern, re.IGNORECASE)
                                for pattern in self.DANGEROUS_PATTERNS]

    def validate_tool_source(self, source_code: str, tool_name: str) -> List[str]:
        """
        Validate tool source code for safety and correctness.

        Args:
            source_code: The Python source code to validate.
            tool_name: Expected name of the tool.

        Returns:
            List[str]: List of validation errors (empty if valid).
        """
        errors = []

        # Basic sanity checks
        if not source_code or not source_code.strip():
            errors.append("Source code is empty")
            return errors

        # Check for dangerous patterns
        for i, regex in enumerate(self.dangerous_regexes):
            if regex.search(source_code):
                errors.append(f"Potentially dangerous code pattern detected: {self.DANGEROUS_PATTERNS[i]}")

        # Try to parse the AST
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            errors.append(f"Invalid Python syntax: {str(e)}")
            return errors  # Can't do further validation if syntax is invalid

        # Check for BaseTool inheritance and required methods
        class_defs = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        if not class_defs:
            errors.append("No class definitions found")
            return errors

        # Look for a class that inherits from BaseTool
        base_tool_class = None
        for class_def in class_defs:
            for base in class_def.bases:
                if (isinstance(base, ast.Name) and base.id == "BaseTool") or \
                   (isinstance(base, ast.Attribute) and base.attr == "BaseTool"):
                    base_tool_class = class_def
                    break
            if base_tool_class:
                break

        if not base_tool_class:
            errors.append("No class inheriting from BaseTool found")

        # Check that the class name matches expected pattern (optional but good practice)
        if base_tool_class:
            expected_class_name = ''.join(word.capitalize() for word in tool_name.split('_')) + 'Tool'
            if base_tool_class.name != expected_class_name:
                # Warning, not error - but we could make it an error if strict
                pass  # We'll allow flexibility in naming

        # Check for required __init__ method
        init_methods = [node for node in base_tool_class.body
                       if isinstance(node, ast.FunctionDef) and node.name == "__init__"]
        if not init_methods:
            errors.append("Missing __init__ method")

        # Check for required execute method
        execute_methods = [node for node in base_tool_class.body
                          if isinstance(node, ast.FunctionDef) and node.name == "execute"]
        if not execute_methods:
            errors.append("Missing execute method")
        else:
            # Validate execute method signature (basic check)
            execute_method = execute_methods[0]
            # Should have at least 'self' parameter
            if len(execute_method.args.args) < 1 or execute_method.args.args[0].arg != 'self':
                errors.append("execute method must have 'self' as first parameter")

        return errors

    def validate_tool_instance(self, tool_instance: Any, tool_name: str) -> List[str]:
        """
        Validate a tool instance for correct interface implementation.

        Args:
            tool_instance: Instance of the tool to validate.
            tool_name: Expected name of the tool.

        Returns:
            List[str]: List of validation errors (empty if valid).
        """
        errors = []

        # Check that it's actually a BaseTool instance
        if not isinstance(tool_instance, BaseTool):
            errors.append(f"Tool instance does not inherit from BaseTool")
            return errors

        # Check that the name matches (if provided)
        if hasattr(tool_instance, 'name') and tool_instance.name != tool_name:
            errors.append(f"Tool name mismatch: expected '{tool_name}', got '{tool_instance.name}'")

        # Check that execute method exists and is callable
        if not hasattr(tool_instance, 'execute') or not callable(getattr(tool_instance, 'execute', None)):
            errors.append("Tool instance missing or non-callable execute method")

        return errors