"""
Base tool interface for AIOS platform.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Abstract base class for all AIOS tools."""

    def __init__(self, name: str, description: str = ""):
        """
        Initialize the tool.

        Args:
            name: Name of the tool.
            description: Description of the tool.
        """
        self.name = name
        self.description = description

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """
        Execute the tool.

        Args:
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            Any: Tool execution result.
        """
        pass

    def get_info(self) -> dict:
        """
        Get information about the tool.

        Returns:
            dict: Tool information.
        """
        return {
            "name": self.name,
            "description": self.description
        }