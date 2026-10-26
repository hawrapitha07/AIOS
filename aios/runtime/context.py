"""
Runtime context for AIOS platform.
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..managers.workflow_manager import WorkflowManager
    from ..managers.model_manager import ModelManager
    from ..knowledge.manager import KnowledgeManager
    from ..tools.registry import ToolRegistry

from ..models.base import Message


class RuntimeContext:
    """Runtime context that holds shared state during workflow execution."""

    def __init__(self):
        """Initialize the runtime context."""
        self.project_config: Optional[Dict[str, Any]] = None
        self.conversation_history: List[Message] = []
        self.metadata: Dict[str, Any] = {}
        self.available_tools: Dict[str, Any] = {}
        self.knowledge_sources: Dict[str, Any] = {}
        self.model_manager: Optional["ModelManager"] = None
        self.workflow_manager: Optional["WorkflowManager"] = None
        self.knowledge_manager: Optional["KnowledgeManager"] = None
        self.tool_registry: Optional["ToolRegistry"] = None

    def set_project_config(self, config: Dict[str, Any]) -> None:
        """
        Set the project configuration.

        Args:
            config: Project configuration dictionary.
        """
        self.project_config = config

    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to the conversation history.

        Args:
            role: Role of the message sender.
            content: Content of the message.
        """
        from ..models.base import Message
        self.conversation_history.append(Message(role=role, content=content))

    def get_conversation_history(self) -> List[Message]:
        """
        Get the conversation history.

        Returns:
            List[Message]: List of conversation messages.
        """
        return self.conversation_history.copy()

    def clear_conversation_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history.clear()

    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set metadata value.

        Args:
            key: Metadata key.
            value: Metadata value.
        """
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get metadata value.

        Args:
            key: Metadata key.
            default: Default value if key not found.

        Returns:
            Any: Metadata value or default.
        """
        return self.metadata.get(key, default)

    def set_knowledge_manager(self, knowledge_manager: "KnowledgeManager") -> None:
        """
        Set the knowledge manager.

        Args:
            knowledge_manager: Knowledge manager instance.
        """
        self.knowledge_manager = knowledge_manager

    def register_knowledge_source(self, name: str, source: Any) -> None:
        """
        Register a knowledge source.

        Args:
            name: Knowledge source name.
            source: Knowledge source instance.
        """
        self.knowledge_sources[name] = source

    def get_knowledge_source(self, name: str) -> Optional[Any]:
        """
        Get a knowledge source by name.

        Args:
            name: Knowledge source name.

        Returns:
            Any: Knowledge source instance or None if not found.
        """
        return self.knowledge_sources.get(name)

    def search_knowledge_sources(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search all registered knowledge sources for the given query.
        """

        all_results = []

        # Search sources registered directly in the context
        for name, source in self.knowledge_sources.items():
            if hasattr(source, "search"):
                try:
                    results = source.search(query, top_k)

                    for result in results:
                        result["source"] = name

                    all_results.extend(results)
                except Exception:
                    continue

        # Search sources registered through KnowledgeManager
        if self.knowledge_manager is not None:
            for name in self.knowledge_manager.list():
                # Avoid searching the same source twice
                if name in self.knowledge_sources:
                    continue

                try:
                    source = self.knowledge_manager.get(name)
                    results = source.search(query, top_k)

                    for result in results:
                        result["source"] = name

                    all_results.extend(results)
                except Exception:
                    continue

        all_results.sort(
            key=lambda x: x.get("score", 0),
            reverse=True
        )

        return all_results[:top_k]

    def refresh_tools(self) -> None:
        """
        Refresh the available tools by rediscovering and reloading them from the filesystem.
        """
        if self.tool_registry is not None:
            self.available_tools = self.tool_registry.load_all_tools()