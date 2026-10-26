from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseKnowledge(ABC):
    """Base interface for all AIOS knowledge sources."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def add(self, content: str, metadata: Dict[str, Any] | None = None):
        """Add content to the knowledge source."""
        pass

    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search the knowledge source."""
        pass