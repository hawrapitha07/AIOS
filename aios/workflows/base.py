"""
Base workflow abstraction for AIOS platform.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict
from ..runtime.context import RuntimeContext


class BaseWorkflow(ABC):
    """Abstract base class for AIOS workflows."""

    def __init__(self, name: str, description: str = ""):
        """
        Initialize the workflow.

        Args:
            name: Name of the workflow.
            description: Description of the workflow.
        """
        self.name = name
        self.description = description

    @abstractmethod
    def run(self, input_data: Any, context: Optional[RuntimeContext] = None) -> Any:
        """
        Execute the workflow.

        Args:
            input_data: Input data for the workflow.
            context: Optional runtime context.

        Returns:
            Any: Workflow output/result.
        """
        pass

    def get_info(self) -> Dict[str, str]:
        """
        Get information about the workflow.

        Returns:
            Dict[str, str]: Workflow information.
        """
        return {
            "name": self.name,
            "description": self.description
        }