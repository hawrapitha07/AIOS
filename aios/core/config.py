"""
AIOS Configuration Management
"""

import os
from typing import Any, Dict, List, Optional
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, validator


class ModelConfig(BaseModel):
    """Configuration for AI model provider."""
    provider: str = Field(default="ollama", description="Model provider name")
    name: str = Field(default="llama3.2:3b", description="Model name")
    temperature: float = Field(default=0.7, description="Sampling temperature")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens to generate")


class DeveloperConfig(BaseModel):
    """Configuration for the Developer Agent."""
    model: ModelConfig = Field(default_factory=ModelConfig)


class DocumentKnowledgeConfig(BaseModel):
    """Configuration for document knowledge source."""
    type: str = Field(default="document", description="Knowledge source type")
    name: str = Field(description="Unique name for the knowledge source")
    path: str = Field(description="Path to the document file")


class KnowledgeConfig(BaseModel):
    """Configuration for knowledge sources."""
    sources: List[DocumentKnowledgeConfig] = Field(default_factory=list)


class WorkflowConfig(BaseModel):
    """Configuration for workflow execution."""
    name: str = Field(default="chatbot", description="Workflow name to execute")


class AIOSConfig(BaseModel):
    """Main AIOS application configuration."""
    name: str = Field(default="aios-app", description="Application name")
    model: ModelConfig = Field(default_factory=ModelConfig)
    developer: DeveloperConfig = Field(default_factory=DeveloperConfig)
    workflow: WorkflowConfig = Field(default_factory=WorkflowConfig)
    knowledge: KnowledgeConfig = Field(default_factory=KnowledgeConfig)



def load_config(config_path: Optional[str] = None) -> AIOSConfig:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to configuration file. If None, looks for aios.yaml in current directory.

    Returns:
        AIOSConfig: Loaded configuration object.

    Raises:
        FileNotFoundError: If configuration file doesn't exist.
        yaml.YAMLError: If configuration file is invalid YAML.
    """
    if config_path is None:
        config_path = "aios.yaml"

    config_file = Path(config_path)
    if not config_file.exists():
        # Return default config if file doesn't exist
        return AIOSConfig()

    with open(config_file, 'r') as f:
        config_data = yaml.safe_load(f)

    return AIOSConfig(**config_data)


def save_config(config: AIOSConfig, config_path: str = "aios.yaml") -> None:
    """
    Save configuration to YAML file.

    Args:
        config: AIOSConfig object to save.
        config_path: Path where to save the configuration file.
    """
    config_dict = config.model_dump()
    with open(config_path, 'w') as f:
        yaml.dump(config_dict, f, default_flow_style=False)


def load_env_vars() -> Dict[str, str]:
    """
    Load environment variables from .env file.

    Returns:
        Dict[str, str]: Dictionary of environment variables.
    """
    env_path = Path(".env")
    env_vars = {}

    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()

    return env_vars