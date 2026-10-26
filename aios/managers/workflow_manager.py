"""
Workflow manager for AIOS platform.
Handles workflow registration, discovery, and execution.
"""

from typing import Dict, Any, Optional
from ..workflows.base import BaseWorkflow
from ..core.exceptions import WorkflowNotFoundError
from ..core.registry import WorkflowRegistry


class WorkflowManager:
    """Manages AIOS workflows."""

    def __init__(self):
        self.workflow_registry = WorkflowRegistry()

    def register_workflow(self, workflow: BaseWorkflow) -> None:
        """
        Register a workflow.

        Args:
            workflow: Workflow instance to register.
        """
        self.workflow_registry.register(workflow.name, workflow)

    def unregister_workflow(self, name: str) -> None:
        """
        Unregister a workflow by name.

        Args:
            name: Name of the workflow to unregister.
        """
        self.workflow_registry.unregister(name)

    def get_workflow(self, name: str) -> BaseWorkflow:
        """
        Get a workflow by name.

        Args:
            name: Name of the workflow to retrieve.

        Returns:
            BaseWorkflow: Workflow instance.

        Raises:
            WorkflowNotFoundError: If workflow is not found.
        """
        try:
            return self.workflow_registry.get(name)
        except Exception as e:
            raise WorkflowNotFoundError(f"Workflow '{name}' not found") from e

    def list_workflows(self) -> Dict[str, BaseWorkflow]:
        """
        List all registered workflows.

        Returns:
            Dict[str, BaseWorkflow]: Dictionary of workflow names to instances.
        """
        return self.workflow_registry.list()

    def workflow_exists(self, name: str) -> bool:
        """
        Check if a workflow exists.

        Args:
            name: Name of the workflow to check.

        Returns:
            bool: True if workflow exists, False otherwise.
        """
        return self.workflow_registry.contains(name)

    def run_workflow(self, name: str, input_data: Any, context: Optional[Any] = None) -> Any:
        """
        Run a workflow by name.

        Args:
            name: Name of the workflow to run.
            input_data: Input data for the workflow.
            context: Optional runtime context.

        Returns:
            Any: Workflow output/result.

        Raises:
            WorkflowNotFoundError: If workflow is not found.
        """
        workflow = self.get_workflow(name)
        return workflow.run(input_data, context)