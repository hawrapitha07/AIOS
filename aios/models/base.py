"""
Base model abstraction for AIOS platform.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class Message:
    """Represents a message in a conversation."""

    def __init__(self, role: str, content: str):
        """
        Initialize a message.

        Args:
            role: Role of the message sender (system, user, assistant).
            content: Content of the message.
        """
        self.role = role
        self.content = content

    def to_dict(self) -> Dict[str, str]:
        """
        Convert message to dictionary.

        Returns:
            Dict[str, str]: Dictionary representation of the message.
        """
        return {"role": self.role, "content": self.content}

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "Message":
        """
        Create message from dictionary.

        Args:
            data: Dictionary with 'role' and 'content' keys.

        Returns:
            Message: Created message instance.
        """
        return cls(role=data["role"], content=data["content"])

    def __repr__(self) -> str:
        return f"Message(role='{self.role}', content='{self.content[:50]}...')"


class BaseModel(ABC):
    """Abstract base class for AI models."""

    def __init__(self, name: str, **kwargs):
        """
        Initialize the model.

        Args:
            name: Name of the model.
            **kwargs: Additional model-specific parameters.
        """
        self.name = name
        self.config = kwargs

    @abstractmethod
    def generate(self, messages: List[Message], **kwargs) -> str:
        """
        Generate a response from the model.

        Args:
            messages: List of conversation messages.
            **kwargs: Additional generation parameters.

        Returns:
            str: Generated response text.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the model is available and ready to use.

        Returns:
            bool: True if model is available, False otherwise.
        """
        pass

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the model.

        Returns:
            Dict[str, Any]: Model information.
        """
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "config": self.config
        }