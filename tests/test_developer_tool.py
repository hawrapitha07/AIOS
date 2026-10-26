import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, Mock

from aios.developer.intent import DeveloperIntent, DeveloperAction
from aios.developer.operations import DeveloperOperationExecutor
from aios.developer.agent import DeveloperAgent
from aios.core.exceptions import AIOSException
from aios.core.config import load_config, AIOSConfig
import json


def test_create_tool_valid_name():
    """Test creating a tool with a valid name."""
    executor = DeveloperOperationExecutor()

    # Create intent for tool creation
    intent = DeveloperIntent(
        action=DeveloperAction.CREATE_TOOL,
        name="calculator",
        description="Performs arithmetic calculations",
        parameters_spec={"expression": "string"}
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Change to temp directory to simulate a project
        with patch('pathlib.Path.cwd', return_value=tmpdir):
            result = executor.execute(intent)

            # Check that tool was created
            assert "Tool 'calculator' created successfully" in result
            tool_file = tmpdir / "tools" / "calculator.py"
            assert tool_file.exists()

            # Check that __init__.py was created
            init_file = tmpdir / "tools" / "__init__.py"
            assert init_file.exists()

            # Check tool file content
            content = tool_file.read_text()
            assert "class CalculatorTool" in content
            assert '"calculator"' in content
            assert '"Performs arithmetic calculations"' in content


def test_create_tool_invalid_name():
    """Test creating a tool with an invalid name."""
    executor = DeveloperOperationExecutor()

    # Test with empty name
    intent = DeveloperIntent(
        action=DeveloperAction.CREATE_TOOL,
        name="",
        description="Test tool",
        parameters_spec={}
    )

    with pytest.raises(AIOSException, match="Tool name is required"):
        executor.execute(intent)

    # Test with invalid Python identifier
    intent = DeveloperIntent(
        action=DeveloperAction.CREATE_TOOL,
        name="123invalid",
        description="Test tool",
        parameters_spec={}
    )

    with pytest.raises(AIOSException, match="is not a valid Python identifier"):
        executor.execute(intent)


def test_create_tool_duplicate_name():
    """Test creating a tool that already exists."""
    executor = DeveloperOperationExecutor()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create tools directory and existing tool
        tools_dir = tmpdir / "tools"
        tools_dir.mkdir()
        existing_tool = tools_dir / "calculator.py"
        existing_tool.write_text("# Existing tool")

        # Create __init__.py
        (tools_dir / "__init__.py").write_text("")

        with patch('pathlib.Path.cwd', return_value=tmpdir):
            intent = DeveloperIntent(
                action=DeveloperAction.CREATE_TOOL,
                name="calculator",
                description="Performs arithmetic calculations",
                parameters_spec={"expression": "string"}
            )

            with pytest.raises(AIOSException, match="already exists"):
                executor.execute(intent)


def test_create_tool_with_different_parameters():
    """Test creating tools with different parameter types."""
    executor = DeveloperOperationExecutor()

    test_cases = [
        ("string_param", {"input": "string"}),
        ("int_param", {"count": "integer"}),
        ("float_param", {"price": "float"}),
        ("bool_param", {"flag": "boolean"}),
        ("mixed_params", {"name": "string", "age": "integer", "active": "boolean"})
    ]

    for tool_name, params_spec in test_cases:
        intent = DeveloperIntent(
            action=DeveloperAction.CREATE_TOOL,
            name=tool_name,
            description=f"A tool with {tool_name}",
            parameters_spec=params_spec
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            with patch('pathlib.Path.cwd', return_value=tmpdir):
                result = executor.execute(intent)

                assert f"Tool '{tool_name}' created successfully" in result
                tool_file = tmpdir / "tools" / f"{tool_name}.py"
                assert tool_file.exists()

                # Check that the parameter types are correctly mapped
                content = tool_file.read_text()
                assert f"class {tool_name.capitalize()}Tool" in content
                # Check for parameter type hints in execute method
                for param_name, param_type in params_spec.items():
                    if param_type == "string":
                        assert f"{param_name}: str" in content
                    elif param_type in ["integer", "int"]:
                        assert f"{param_name}: int" in content
                    elif param_type in ["float", "number"]:
                        assert f"{param_name}: float" in content
                    elif param_type in ["boolean", "bool"]:
                        assert f"{param_name}: bool" in content


def test_create_tool_no_parameters():
    """Test creating a tool with no parameters."""
    executor = DeveloperOperationExecutor()

    intent = DeveloperIntent(
        action=DeveloperAction.CREATE_TOOL,
        name="simple_tool",
        description="A simple tool with no parameters",
        parameters_spec={}
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        with patch('pathlib.Path.cwd', return_value=tmpdir):
            result = executor.execute(intent)

            assert "Tool 'simple_tool' created successfully" in result
            tool_file = tmpdir / "tools" / "simple_tool.py"
            assert tool_file.exists()

            content = tool_file.read_text()
            assert "class SimpleTool" in content
            assert 'def execute(self) -> Any:' in content  # No parameters


class TestDeveloperAgent:
    """Test the Developer Agent's intent parsing."""

    @classmethod
    def setup_class(cls):
        # Set up a mapping from request to expected (provider, model)
        cls.request_to_expected = {
            "switch my model to openai's gpt-4o": ("openai", "gpt-4o"),
            "change my model to OpenAI gpt-4o-mini": ("openai", "gpt-4o-mini"),
            "switch to ollama llama3.2:3b": ("ollama", "llama3.2:3b"),
            "change my model to llama3.2:3b": ("ollama", "llama3.2:3b"),  # Assuming current provider is ollama
        }

    def test_model_switching_intent(self):
        """Test that the Developer Agent correctly parses model switching requests."""
        for request, (expected_provider, expected_model) in self.request_to_expected.items():
            with patch('aios.developer.agent.ModelManager') as MockModelManager:
                # Setup the mock model manager to return a mock model when create_model is called
                mock_model = Mock()
                MockModelManager.return_value.create_model.return_value = mock_model

                # We need to mock the generate method of the model to return a JSON string
                # based on the request.
                def generate_side_effect(messages):
                    # The user's request is the last message in the list
                    user_request = messages[-1].content
                    # Look up the expected provider and model for this request
                    provider, model = self.request_to_expected.get(user_request, ("mock", "default"))
                    response_json = {
                        "action": "set_model",
                        "provider": provider,
                        "model": model,
                        "parameters": {}
                    }
                    return json.dumps(response_json)

                mock_model.generate.side_effect = generate_side_effect

                agent = DeveloperAgent()
                intent = agent.process_request(request)

                assert intent.provider == expected_provider, \
                    f"For request '{request}': expected provider {expected_provider}, got {intent.provider}"
                assert intent.model == expected_model, \
                    f"For request '{request}': expected model {expected_model}, got {intent.model}"

    def test_set_model_operation(self):
        """Test that the Developer Agent can execute a set_model operation."""
        # We'll test the execute_request method by mocking the operation executor
        with patch('aios.developer.agent.DeveloperAgent.process_request') as mock_process_request, \
             patch('aios.developer.agent.DeveloperOperationExecutor.execute') as mock_execute:

            # Set up the mock to return a set_model intent
            mock_intent = Mock()
            mock_intent.action = 'set_model'
            mock_intent.provider = 'openai'
            mock_intent.model = 'gpt-4o'
            mock_process_request.return_value = mock_intent

            # Set up the mock executor to return a success message
            mock_execute.return_value = "Model updated to provider: openai, name: gpt-4o"

            agent = DeveloperAgent()
            result = agent.execute_request("switch my model to openai's gpt-4o")

            # Check that the operation executor was called with the intent
            mock_execute.assert_called_once()
            # Check that the result is the success message
            assert "Model updated to provider: openai, name: gpt-4o" in result