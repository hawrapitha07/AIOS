"""
Tests for AIOS model system.
"""

import pytest
from aios.models.base import Message
from aios.models.providers.mock import MockModel
from aios.managers.model_manager import ModelManager
from aios.core.exceptions import ModelProviderError


def test_mock_model():
    """Test mock model basic functionality."""
    model = MockModel(name="test-model")

    # Test message creation
    msg = Message(role="user", content="Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"

    # Test model generation
    messages = [Message(role="user", content="Hello")]
    response = model.generate(messages)
    assert isinstance(response, str)
    assert len(response) > 0
    assert "Mock response" in response

    # Test model info
    info = model.get_info()
    assert info["name"] == "test-model"
    assert info["type"] == "MockModel"

    # Test availability
    assert model.is_available() is True


def test_model_manager():
    """Test model manager functionality."""
    manager = ModelManager()

    # Test listing providers
    providers = manager.list_providers()
    assert "mock" in providers
    assert "openai" in providers  # May be available depending on installation

    # Test creating mock model
    model = manager.create_model("mock", "test")
    assert model is not None
    assert model.name == "test"

    # Test getting cached model
    cached_model = manager.get_model("mock", "test")
    assert cached_model is model  # Should be the same instance

    # Test unavailable provider
    with pytest.raises(ModelProviderError):
        manager.create_model("nonexistent", "test")


def test_message_serialization():
    """Test message to/from dict conversion."""
    msg = Message(role="assistant", content="Hello world")

    # To dict
    msg_dict = msg.to_dict()
    assert msg_dict == {"role": "assistant", "content": "Hello world"}

    # From dict
    msg2 = Message.from_dict(msg_dict)
    assert msg2.role == msg.role
    assert msg2.content == msg.content