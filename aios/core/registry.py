"""
Component registry for AIOS platform.
Provides a way to register and retrieve components like workflows, models, etc.
"""

from typing import Dict, Type, Any, Optional
from .exceptions import AIOSException


class Registry:
    """Generic registry for AIOS components."""

    def __init__(self, name: str):
        self.name = name
        self._items: Dict[str, Any] = {}

    def register(self, name: str, item: Any) -> None:
        """
        Register an item in the registry.

        Args:
            name: Name to register the item under.
            item: Item to register.
        """
        self._items[name] = item

    def get(self, name: str) -> Any:
        """
        Get an item from the registry.

        Args:
            name: Name of the item to retrieve.

        Returns:
            The registered item.

        Raises:
            AIOSException: If item is not found.
        """
        if name not in self._items:
            raise AIOSException(f"{self.name} '{name}' not found in registry")
        return self._items[name]

    def list(self) -> Dict[str, Any]:
        """
        List all registered items.

        Returns:
            Dictionary of all registered items.
        """
        return self._items.copy()

    def unregister(self, name: str) -> None:
        """
        Unregister an item from the registry.

        Args:
            name: Name of the item to unregister.
        """
        if name in self._items:
            del self._items[name]

    def contains(self, name: str) -> bool:
        """
        Check if an item is registered.

        Args:
            name: Name of the item to check.

        Returns:
            True if item is registered, False otherwise.
        """
        return name in self._items


class WorkflowRegistry(Registry):
    """Registry specifically for workflows."""

    def __init__(self):
        super().__init__("Workflow")


class ModelRegistry(Registry):
    """Registry specifically for models."""

    def __init__(self):
        super().__init__("Model")


# Global registries
workflow_registry = WorkflowRegistry()
model_registry = ModelRegistry()