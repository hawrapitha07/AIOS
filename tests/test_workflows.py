"""
Tests for AIOS workflow system.
"""

import pytest
from aios.workflows.base import BaseWorkflow
from aios.workflows.chatbot.workflow import ChatbotWorkflow
from aios.managers.workflow_manager import WorkflowManager
from aios.core.exceptions import WorkflowNotFoundError
from aios.runtime.context import RuntimeContext
from aios.knowledge.document import DocumentKnowledge
from aios.models.base import Message


class TestWorkflow(BaseWorkflow):
    """Test workflow implementation."""

    def __init__(self):
        super().__init__(name="test-workflow", description="A test workflow")

    def run(self, input_data, context=None):
        return f"Processed: {input_data}"


def test_workflow_base():
    """Test base workflow functionality."""
    workflow = TestWorkflow()
    assert workflow.name == "test-workflow"
    assert workflow.description == "A test workflow"

    result = workflow.run("test input")
    assert result == "Processed: test input"


def test_chatbot_workflow():
    """Test chatbot workflow instantiation."""
    workflow = ChatbotWorkflow()
    assert workflow.name == "chatbot"
    assert "Chatbot" in workflow.description


def test_workflow_manager():
    """Test workflow manager functionality."""
    manager = WorkflowManager()

    # Test registering workflow
    workflow = TestWorkflow()
    manager.register_workflow(workflow)

    # Test listing workflows
    workflows = manager.list_workflows()
    assert "test-workflow" in workflows
    assert workflows["test-workflow"] is workflow

    # Test getting workflow
    retrieved_workflow = manager.get_workflow("test-workflow")
    assert retrieved_workflow is workflow

    # Test workflow existence
    assert manager.workflow_exists("test-workflow") is True
    assert manager.workflow_exists("nonexistent") is False

    # Test running workflow
    result = manager.run_workflow("test-workflow", "input data")
    assert result == "Processed: input data"

    # Test getting nonexistent workflow
    with pytest.raises(WorkflowNotFoundError):
        manager.get_workflow("nonexistent")

    # Test running nonexistent workflow
    with pytest.raises(WorkflowNotFoundError):
        manager.run_workflow("nonexistent", "data")


def test_runtime_context():
    """Test runtime context functionality."""
    context = RuntimeContext()

    # Test initial state
    assert context.project_config is None
    assert len(context.conversation_history) == 0
    assert len(context.metadata) == 0
    assert len(context.available_tools) == 0
    assert len(context.knowledge_sources) == 0

    # Test adding message
    context.add_message("user", "Hello")
    assert len(context.conversation_history) == 1
    assert context.conversation_history[0].role == "user"
    assert context.conversation_history[0].content == "Hello"

    # Test setting metadata
    context.set_metadata("test_key", "test_value")
    assert context.get_metadata("test_key") == "test_value"
    assert context.get_metadata("nonexistent", "default") == "default"

    # Test clearing history
    context.clear_conversation_history()
    assert len(context.conversation_history) == 0


def test_runtime_context_knowledge_sources():
    """Test runtime context knowledge sources functionality."""
    context = RuntimeContext()

    # Test initial state
    assert len(context.knowledge_sources) == 0

    # Test registering knowledge source
    doc_knowledge = DocumentKnowledge("test_kb")
    doc_knowledge.add("AIOS is a Python platform for building AI applications.", {"category": "info"})
    doc_knowledge.add("AIOS supports models, knowledge and workflows.", {"category": "features"})

    context.register_knowledge_source("test_kb", doc_knowledge)
    assert len(context.knowledge_sources) == 1
    assert "test_kb" in context.knowledge_sources

    # Test getting knowledge source
    retrieved_source = context.get_knowledge_source("test_kb")
    assert retrieved_source is doc_knowledge

    # Test searching knowledge sources
    results = context.search_knowledge_sources("AIOS models", top_k=5)
    assert len(results) > 0
    assert results[0]["content"] == "AIOS supports models, knowledge and workflows."
    assert results[0]["score"] > 0
    assert results[0]["source"] == "test_kb"

    # Test searching with no matches
    results = context.search_knowledge_sources("xyzabcnonexistent", top_k=5)
    assert len(results) == 0

    # Test searching with no knowledge sources
    empty_context = RuntimeContext()
    results = empty_context.search_knowledge_sources("any query", top_k=5)
    assert len(results) == 0


def test_chatbot_knowledge_integration():
    """Test chatbot workflow knowledge integration."""
    # Create a mock context with knowledge source
    context = RuntimeContext()

    # Add a knowledge source
    doc_knowledge = DocumentKnowledge("test_kb")
    doc_knowledge.add("AIOS is a Python platform for building AI applications.", {"category": "info"})
    doc_knowledge.add("AIOS supports models, knowledge and workflows.", {"category": "features"})
    doc_knowledge.add("The default model is llama3.2:3b through Ollama.", {"category": "model"})

    context.register_knowledge_source("test_kb", doc_knowledge)

    # Create chatbot workflow
    workflow = ChatbotWorkflow()

    # We can't easily test the full interactive session, but we can test
    # that the knowledge search integration works by testing the context
    # methods that we added

    # Test that knowledge sources are registered
    assert len(context.knowledge_sources) == 1

    # Test searching knowledge sources
    results = context.search_knowledge_sources("AIOS models", top_k=3)
    assert len(results) > 0
    # Should find the document about models, knowledge and workflows (score 2 for matching both "AIOS" and "models")
    models_found = any("models, knowledge and workflows" in result["content"] for result in results)
    assert models_found


def test_chatbot_no_knowledge_sources():
    """Test chatbot works normally when no knowledge sources are registered."""
    context = RuntimeContext()

    # Should have no knowledge sources initially
    assert len(context.knowledge_sources) == 0

    # Search should return empty list
    results = context.search_knowledge_sources("any query", top_k=5)
    assert len(results) == 0