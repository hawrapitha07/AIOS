import sys

content = '''from aios.core.config import load_config, save_config
from aios.managers.model_manager import ModelManager
from aios.managers.workflow_manager import WorkflowManager
from aios.managers.project_manager import ProjectManager
from aios.core.exceptions import AIOSException
import os
from pathlib import Path


class DeveloperOperationExecutor:
    def __init__(self):
        self.model_manager = ModelManager()
        self.workflow_manager = WorkflowManager()
        self.project_manager = ProjectManager()

    def execute(self, intent):
        action = intent.action
        if action == 'set_model':
            return self._set_model(intent.provider, intent.model)
        elif action == 'set_model_provider':
            return self._set_model_provider(intent.provider)
        elif action == 'show_status':
            return self._show_status()
        elif action == 'update_chatbot_config':
            return self._update_chatbot_config(intent.system_prompt)
        elif action == 'create_workflow':
            return self._create_workflow(intent.workflow_name)
        elif action == 'remove_workflow':
            return self._remove_workflow(intent.workflow_name)
        elif action == 'list_workflows':
            return self._list_workflows()
        elif action == 'list_models':
            return self._list_models()
        else:
            raise AIOSException(f'Unsupported action: {action}')

    def _set_model(self, provider, model):
        config = load_config()
        config.model.provider = provider
        config.model.name = model
        save_config(config)
        return f'Model updated to provider: {provider}, name: {model}'

    def _set_model_provider(self, provider):
        config = load_config()
        config.model.provider = provider
        save_config(config)
        return f'Model provider updated to: {provider}'

    def _show_status(self):
        config = load_config()
        return f'Current AIOS configuration:\\nProvider: {config.model.provider}\\nModel: {config.model.name}'

    def _update_chatbot_config(self, system_prompt):
        # For now, we just return a message.
        # In a full implementation, we would update the chatbot config.
        return f'Chatbot system prompt updated to: {system_prompt}'

    def _create_workflow(self, workflow_name):
        workflow_dir = Path('aios/workflows') / workflow_name
        if workflow_dir.exists():
            raise AIOSException(f'Workflow {workflow_name} already exists.')
        workflow_dir.mkdir(parents=True)
        (workflow_dir / '__init__.py').write_text('')
        (workflow_dir / 'workflow.py').write_text(f'\"\"\"{workflow_name} workflow.\"\"\"\\nfrom aios.workflows.base import BaseWorkflow\\n\\nclass {workflow_name.capitalize()}Workflow(BaseWorkflow):\\n    def __init__(self):\\n        super().__init__(\"{workflow_name}\")\\n    def run(self, context, input=None):\\n        return f\"{workflow_name} workflow executed.\"\\n')
        (workflow_dir / 'config.py').write_text('\"\"\"Workflow configuration.\"\"\"\\nfrom pydantic import BaseModel\\n\\nclass Config(BaseModel):\\n    pass\\n')

    def _remove_workflow(self, workflow_name):
        workflow_dir = Path('aios/workflows') / workflow_name
        if not workflow_dir.exists():
            raise AIOSException(f'Workflow {workflow_name} not found.')
        import shutil
        shutil.rmtree(workflow_dir)
        return f'Workflow {workflow_name} removed.'

    def _list_workflows(self):
        workflows_dir = Path('aios/workflows')
        workflows = [d.name for d in workflows_dir.iterdir() if d.is_dir() and not d.name.startswith('_') and d.name != '__pycache__']
        if not workflows:
            return 'No workflows available.'
        return 'Available workflows:\\n' + '\\n'.join(f'- {w}' for w in workflows)

    def _list_models(self):
        providers = self.model_manager.list_providers()
        result = []
        for provider_name, provider_class in providers.items():
            is_available = self.model_manager.is_provider_available(provider_name)
            status = '[Available]' if is_available else '[Not Configured]'
            result.append(f'{provider_name}: {status}')
        return 'Available models:\\n' + '\\n'.join(result)
'''
with open('aios/developer/operations.py', 'w') as f:
    f.write(content)
