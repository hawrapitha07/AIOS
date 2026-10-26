"""
Tests for AIOS configuration system.
"""

import tempfile
import os
from pathlib import Path
import pytest
from aios.core.config import load_config, save_config, AIOSConfig, ModelConfig, WorkflowConfig
from aios.core.exceptions import ConfigurationError


def test_default_config():
    """Test loading default configuration when no file exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            config = load_config()
            assert isinstance(config, AIOSConfig)
            assert config.name == "aios-app"
            assert config.model.provider == "ollama"  # Default provider is now ollama
            assert config.model.name == "llama3.2:3b"  # Default model name
        finally:
            os.chdir(old_cwd)


def test_load_save_config():
    """Test saving and loading configuration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test.yaml"
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)

            # Create and save config
            model_config = ModelConfig(provider="openai", name="gpt-4")
            workflow_config = WorkflowConfig(name="chatbot")
            config = AIOSConfig(name="test-app", model=model_config, workflow=workflow_config)
            save_config(config, str(config_path))

            # Load config
            loaded_config = load_config(str(config_path))
            assert loaded_config.name == "test-app"
            assert loaded_config.model.provider == "openai"
            assert loaded_config.model.name == "gpt-4"
            assert loaded_config.workflow.name == "chatbot"
        finally:
            os.chdir(old_cwd)


def test_any_provider_allowed():
    """Test that any provider is now allowed (validation removed)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test.yaml"
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)

            # Create config with any provider
            config_content = """
name: test-app
model:
  provider: any-provider-name
  name: test-model
workflow:
  name: chatbot
"""
            config_path.write_text(config_content)

            # Should load successfully without raising an exception
            config = load_config(str(config_path))
            assert config.model.provider == "any-provider-name"
            assert config.model.name == "test-model"
        finally:
            os.chdir(old_cwd)