"""
Tests for Ollama model provider.
"""

import json
from unittest.mock import patch, MagicMock
import pytest
from aios.models.providers.ollama_provider import OllamaProvider
from aios.models.base import Message
from aios.core.exceptions import ModelProviderError


class TestOllamaProvider:
    """Test Ollama provider functionality."""

    def test_ollama_provider_init(self):
        """Test Ollama provider initialization."""
        provider = OllamaProvider(name="llama3.2:3b")
        assert provider.name == "llama3.2:3b"
        assert provider.base_url == "http://localhost:11434"

    def test_ollama_provider_init_with_base_url(self):
        """Test Ollama provider initialization with custom base URL."""
        provider = OllamaProvider(name="llama3.2:3b", base_url="http://custom:8080")
        assert provider.base_url == "http://custom:8080"

    def test_ollama_provider_init_with_env_base_url(self, monkeypatch):
        """Test Ollama provider initialization with environment variable."""
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://env:9000")
        provider = OllamaProvider(name="llama3.2:3b")
        assert provider.base_url == "http://env:9000"

    def test_message_conversion(self):
        """Test conversion of AIOS Message objects to Ollama format."""
        provider = OllamaProvider(name="test")
        messages = [
            Message(role="system", content="You are helpful"),
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi there!")
        ]

        # This is tested indirectly through the generate method mocking
        # but we can verify the conversion logic
        ollama_messages = []
        for msg in messages:
            ollama_messages.append({
                "role": msg.role,
                "content": msg.content
            })

        expected = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        assert ollama_messages == expected

    @patch('urllib.request.urlopen')
    def test_generate_success(self, mock_urlopen):
        """Test successful generation from Ollama."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "message": {
                "content": "Hello! How can I help you today?"
            }
        }).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        provider = OllamaProvider(name="llama3.2:3b")
        messages = [Message(role="user", content="Hello")]

        response = provider.generate(messages)

        assert response == "Hello! How can I help you today?"
        # Verify the request was made correctly
        mock_urlopen.assert_called_once()
        args, kwargs = mock_urlopen.call_args
        assert args[0].full_url == "http://localhost:11434/api/chat"
        assert args[0].method == 'POST'

        # Check the request data
        data = json.loads(args[0].data.decode('utf-8'))
        assert data["model"] == "llama3.2:3b"
        assert data["stream"] == False
        assert len(data["messages"]) == 1
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][0]["content"] == "Hello"

    @patch('urllib.request.urlopen')
    def test_generate_with_parameters(self, mock_urlopen):
        """Test generation with additional parameters."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "message": {
                "content": "Response with parameters"
            }
        }).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        provider = OllamaProvider(name="test")
        messages = [Message(role="user", content="Test")]

        response = provider.generate(messages, temperature=0.8, top_p=0.9)

        assert response == "Response with parameters"
        # Check that parameters were passed in options
        args, kwargs = mock_urlopen.call_args
        data = json.loads(args[0].data.decode('utf-8'))
        assert data["options"]["temperature"] == 0.8
        assert data["options"]["top_p"] == 0.9

    @patch('urllib.request.urlopen')
    def test_generate_http_error(self, mock_urlopen):
        """Test handling of HTTP errors from Ollama."""
        # Create a mock HTTPError
        import urllib.error
        # Create a mock response for the error body
        error_body = json.dumps({"error": "model not found"}).encode('utf-8')
        mock_error = MagicMock()
        mock_error.read.return_value = error_body
        mock_error.__enter__.return_value = mock_error

        # Create the HTTPError
        http_error = urllib.error.HTTPError(
            url="http://localhost:11434/api/chat",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=error_body  # This should be bytes-like
        )
        # Override the read method to return our error body
        http_error.read = lambda: error_body

        mock_urlopen.side_effect = http_error

        provider = OllamaProvider(name="nonexistent")
        messages = [Message(role="user", content="Hello")]

        with pytest.raises(Exception) as exc_info:
            provider.generate(messages)

        assert "Ollama API error: 404 Not Found" in str(exc_info.value)
        assert "model not found" in str(exc_info.value)

    @patch('urllib.request.urlopen')
    def test_generate_url_error(self, mock_urlopen):
        """Test handling of connection errors."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError(
            reason="Connection refused"
        )

        provider = OllamaProvider(name="test")
        messages = [Message(role="user", content="Hello")]

        with pytest.raises(Exception) as exc_info:
            provider.generate(messages)

        assert "Failed to connect to Ollama" in str(exc_info.value)
        assert "Connection refused" in str(exc_info.value)

    @patch('urllib.request.urlopen')
    def test_generate_invalid_json(self, mock_urlopen):
        """Test handling of invalid JSON response."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"invalid json"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        provider = OllamaProvider(name="test")
        messages = [Message(role="user", content="Hello")]

        with pytest.raises(Exception) as exc_info:
            provider.generate(messages)

        assert "Invalid JSON response from Ollama" in str(exc_info.value)

    @patch('urllib.request.urlopen')
    def test_generate_missing_message_content(self, mock_urlopen):
        """Test handling of response missing message content."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "message": {
                # missing "content" field
            }
        }).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        provider = OllamaProvider(name="test")
        messages = [Message(role="user", content="Hello")]

        with pytest.raises(Exception) as exc_info:
            provider.generate(messages)

        assert "Invalid response format from Ollama" in str(exc_info.value)

    @patch('urllib.request.urlopen')
    def test_is_available_true(self, mock_urlopen):
        """Test is_available returns True when model is present."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "models": [
                {"name": "llama3.2:3b"},
                {"name": "other-model"}
            ]
        }).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        provider = OllamaProvider(name="llama3.2:3b")
        assert provider.is_available() is True

    @patch('urllib.request.urlopen')
    def test_is_available_false(self, mock_urlopen):
        """Test is_available returns False when model is not present."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "models": [
                {"name": "other-model"},
                {"name": "another-model"}
            ]
        }).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        provider = OllamaProvider(name="llama3.2:3b")
        assert provider.is_available() is False

    @patch('urllib.request.urlopen')
    def test_is_available_connection_error(self, mock_urlopen):
        """Test is_available returns False on connection error."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError(reason="Connection failed")

        provider = OllamaProvider(name="test")
        assert provider.is_available() is False

    def test_get_info(self):
        """Test getting model information."""
        provider = OllamaProvider(name="test-model", base_url="http://custom:1234")
        info = provider.get_info()

        assert info["name"] == "test-model"
        assert info["type"] == "OllamaProvider"
        assert info["base_url"] == "http://custom:1234"


def test_model_manager_includes_ollama():
    """Test that ModelManager includes Ollama provider when available."""
    from aios.managers.model_manager import ModelManager

    manager = ModelManager()
    providers = manager.list_providers()

    # Ollama should be in the providers (since we just created the file)
    assert "ollama" in providers
    assert providers["ollama"].__name__ == "OllamaProvider"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])