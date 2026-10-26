"""
Model manager for AIOS platform.
Handles model provider selection and instantiation.
"""

from typing import Dict, Any, Optional, Type
from ..models.base import BaseModel
from ..models.providers.mock import MockModel
from ..models.providers.openai_provider import OpenAIProvider
from ..core.exceptions import ModelProviderError
from ..core.registry import ModelRegistry


class ModelManager:
    """Manages AI model providers and instantiation."""

    def __init__(self):
        self.provider_classes: Dict[str, Type[BaseModel]] = {
            "mock": MockModel,
            "openai": OpenAIProvider,
        }
        # Try to add Ollama if available
        try:
            from ..models.providers.ollama_provider import OllamaProvider
            self.provider_classes["ollama"] = OllamaProvider
        except ImportError:
            pass  # Ollama not available, that's okay

        self._instances: Dict[str, BaseModel] = {}
        self.model_registry = ModelRegistry()

    def register_provider(self, name: str, provider_class: Type[BaseModel]) -> None:
        """
        Register a model provider class.

        Args:
            name: Name of the provider.
            provider_class: Provider class to register.
        """
        self.provider_classes[name] = provider_class

    def create_model(self, provider: str, name: str, **kwargs) -> BaseModel:
        """
        Create a model instance.

        Args:
            provider: Provider name (mock, openai, etc.).
            name: Model name.
            **kwargs: Additional parameters for the model.

        Returns:
            BaseModel: Created model instance.

        Raises:
            ModelProviderError: If provider is not supported.
        """
        if provider not in self.provider_classes:
            raise ModelProviderError(f"Unsupported model provider: {provider}")

        provider_class = self.provider_classes[provider]
        model_instance = provider_class(name=name, **kwargs)

        # Cache the instance
        cache_key = f"{provider}:{name}"
        self._instances[cache_key] = model_instance

        return model_instance

    def get_model(self, provider: str, name: str) -> Optional[BaseModel]:
        """
        Get a cached model instance.

        Args:
            provider: Provider name.
            name: Model name.

        Returns:
            BaseModel: Cached model instance or None if not found.
        """
        cache_key = f"{provider}:{name}"
        return self._instances.get(cache_key)

    def list_providers(self) -> Dict[str, Type[BaseModel]]:
        """
        List all registered model providers.

        Returns:
            Dict[str, Type[BaseModel]]: Dictionary of provider names to classes.
        """
        return self.provider_classes.copy()

    def is_provider_available(self, provider: str) -> bool:
        """
        Check if a provider is available.

        Args:
            provider: Provider name to check.

        Returns:
            bool: True if provider is available, False otherwise.
        """
        if provider not in self.provider_classes:
            return False

        # For providers that need API keys, check if they're configured
        if provider == "openai":
            import os
            from pathlib import Path

            # Check environment variable first
            api_key = os.getenv("OPENAI_API_KEY")

            # If not in environment, check .env file
            if not api_key:
                env_path = Path.cwd() / ".env"
                if env_path.exists():
                    with open(env_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and '=' in line:
                                key, value = line.split('=', 1)
                                if key.strip() == "OPENAI_API_KEY":
                                    api_key = value.strip()
                                    break

            return bool(api_key)
        elif provider == "anthropic":
            import os
            from pathlib import Path

            # Check environment variable first
            api_key = os.getenv("ANTHROPIC_API_KEY")

            # If not in environment, check .env file
            if not api_key:
                env_path = Path.cwd() / ".env"
                if env_path.exists():
                    with open(env_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and '=' in line:
                                key, value = line.split('=', 1)
                                if key.strip() == "ANTHROPIC_API_KEY":
                                    api_key = value.strip()
                                    break

            return bool(api_key)
        elif provider == "google":
            import os
            from pathlib import Path

            # Check environment variable first
            api_key = os.getenv("GOOGLE_API_KEY")

            # If not in environment, check .env file
            if not api_key:
                env_path = Path.cwd() / ".env"
                if env_path.exists():
                    with open(env_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and '=' in line:
                                key, value = line.split('=', 1)
                                if key.strip() == "GOOGLE_API_KEY":
                                    api_key = value.strip()
                                    break

            return bool(api_key)

        return True