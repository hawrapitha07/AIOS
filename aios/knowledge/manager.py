from typing import Dict, List, Optional
from pathlib import Path
import os

from aios.knowledge.base import BaseKnowledge
from aios.knowledge.document import DocumentKnowledge
from aios.core.exceptions import AIOSException


class KnowledgeManager:
    """Manages AIOS knowledge sources."""

    def __init__(self):
        self._knowledge: Dict[str, BaseKnowledge] = {}

    def register(self, knowledge: BaseKnowledge):
        """Register a knowledge source."""
        if knowledge.name in self._knowledge:
            raise AIOSException(
                f"Knowledge source '{knowledge.name}' already exists."
            )

        self._knowledge[knowledge.name] = knowledge

    def get(self, name: str) -> BaseKnowledge:
        """Get a registered knowledge source."""
        if name not in self._knowledge:
            raise AIOSException(
                f"Knowledge source '{name}' not found."
            )

        return self._knowledge[name]

    def list(self):
        """List registered knowledge sources."""
        return list(self._knowledge.keys())

    def remove(self, name: str):
        """Remove a knowledge source."""
        if name not in self._knowledge:
            raise AIOSException(
                f"Knowledge source '{name}' not found."
            )

        del self._knowledge[name]

    def load_from_config(self, knowledge_config: KnowledgeConfig, project_dir: Optional[Path] = None) -> None:
        """
        Load knowledge sources from configuration.

        Args:
            knowledge_config: Knowledge configuration from AIOSConfig
            project_dir: Project directory for resolving relative paths. If None, uses current working directory.
        """
        if project_dir is None:
            project_dir = Path.cwd()

        for source_config in knowledge_config.sources:
            if source_config.type == "document":
                # Create DocumentKnowledge instance
                knowledge = DocumentKnowledge(source_config.name)

                # Resolve path: if absolute, use as is; if relative, resolve relative to project directory
                configured_path = Path(source_config.path)
                if configured_path.is_absolute():
                    file_path = configured_path
                else:
                    file_path = project_dir / configured_path

                # Check if file exists
                if not file_path.exists():
                    raise AIOSException(
                        f"Knowledge file not found: {file_path}. "
                        f"Configured for knowledge source '{source_config.name}'"
                    )

                # Load file content
                try:
                    content = file_path.read_text(encoding='utf-8')
                    knowledge.add(content, {"source": str(file_path)})
                except Exception as e:
                    raise AIOSException(
                        f"Failed to load knowledge file {file_path}: {e}"
                    )

                # Register the knowledge source
                self.register(knowledge)
            else:
                raise AIOSException(
                    f"Unsupported knowledge source type: {source_config.type}. "
                    f"Only 'document' type is currently supported."
                )