"""
Agent runtime for AIOS platform.
Orchestrates workflow execution with access to models, knowledge, and tools.
"""

from typing import Any, Optional, Dict, List
from ..models.base import BaseModel, Message
from ..managers.model_manager import ModelManager
from ..managers.workflow_manager import WorkflowManager
from ..runtime.context import RuntimeContext
from ..core.exceptions import ModelProviderError


class AgentRuntime:
    """Agent runtime that orchestrates workflow execution."""

    def __init__(self, model_manager: ModelManager, workflow_manager: WorkflowManager):
        """
        Initialize the agent runtime.

        Args:
            model_manager: Model manager instance.
            workflow_manager: Workflow manager instance.
        """
        self.model_manager = model_manager
        self.workflow_manager = workflow_manager

    def create_context(self) -> RuntimeContext:
        """
        Create a new runtime context.

        Returns:
            RuntimeContext: New runtime context instance.
        """
        context = RuntimeContext()
        context.model_manager = self.model_manager
        context.workflow_manager = self.workflow_manager
        # Initialize tool registry and load available tools
        from aios.tools.registry import ToolRegistry
        context.tool_registry = ToolRegistry()
        # Load all available tools into the context
        context.available_tools = context.tool_registry.load_all_tools()
        return context

    def get_model(self, provider: str, name: str) -> BaseModel:
        """
        Get a model instance from the model manager.

        Args:
            provider: Model provider name.
            name: Model name.

        Returns:
            BaseModel: Model instance.

        Raises:
            ModelProviderError: If model cannot be created or retrieved.
        """
        # Try to get cached instance first
        model = self.model_manager.get_model(provider, name)
        if model is not None:
            return model

        # Create new instance
        try:
            model = self.model_manager.create_model(provider=provider, name=name)
            return model
        except Exception as e:
            raise ModelProviderError(f"Failed to create model {provider}:{name}: {str(e)}")

    def run_workflow(self, workflow_name: str, input_data: Any, context: Optional[RuntimeContext] = None) -> Any:
        """
        Run a workflow using the workflow manager.

        Args:
            workflow_name: Name of the workflow to run.
            input_data: Input data for the workflow.
            context: Optional runtime context.

        Returns:
            Any: Workflow output/result.
        """
        return self.workflow_manager.run_workflow(workflow_name, input_data, context)