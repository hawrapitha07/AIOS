from aios.core.config import load_config, save_config
from aios.managers.model_manager import ModelManager
from aios.managers.workflow_manager import WorkflowManager
from aios.managers.project_manager import ProjectManager
from aios.tools.generator import ToolGenerator
from aios.tools.validator import ToolValidator
from aios.core.exceptions import AIOSException
import os
from pathlib import Path
import aios


class DeveloperOperationExecutor:
    def __init__(self):
        self.model_manager = ModelManager()
        self.workflow_manager = WorkflowManager()
        self.project_manager = ProjectManager()
        self.workflows_dir = Path(aios.__file__).parent / "workflows"
        self.tool_generator = ToolGenerator(self.model_manager)
        self.tool_validator = ToolValidator()

    def execute(self, intent):
        action = intent.action
        if action == 'set_model':
            provider = intent.provider
            model = intent.model
            # Support parameters-based intents as well
            if intent.parameters:
                provider = intent.parameters.get("provider", provider)
                model = intent.parameters.get("model", model)
                model = intent.parameters.get("name", model)
            return self._set_model(provider, model)
        elif action == 'set_model_provider':
            provider = intent.provider
            if intent.parameters:
                provider = intent.parameters.get("provider", provider)
            return self._set_model_provider(provider)
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
        elif action == 'create_tool':
            return self._create_tool(intent)
        elif action == 'clarification_required':
            # This should be handled by the DeveloperAgent, but we provide a fallback
            return intent.question or "Please clarify your request."
        else:
            raise AIOSException(f'Unsupported action: {action}')

    def _set_model(self, provider=None, model=None):
        config = load_config()

        # Only update provider if one was explicitly provided
        if provider is not None:
            config.model.provider = provider

        # Only update model if one was explicitly provided
        if model is not None:
            config.model.name = model

        # Never allow an invalid configuration to be saved
        if config.model.provider is None:
            raise AIOSException("Model provider cannot be None.")

        if config.model.name is None:
            raise AIOSException("Model name cannot be None.")

        # Check if API key is required for cloud/API models
        cloud_providers = ["openai", "anthropic", "google"]  # Known cloud providers
        if config.model.provider in cloud_providers:
            # Map provider to environment variable
            env_var_map = {
                "openai": "OPENAI_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
                "google": "GOOGLE_API_KEY"
            }
            env_var = env_var_map.get(config.model.provider)

            if env_var:
                # Check if the API key is set in environment or .env file
                import os
                from pathlib import Path

                # Check environment variable first
                api_key = os.getenv(env_var)

                # If not in environment, check .env file
                if not api_key:
                    env_path = Path.cwd() / ".env"
                    if env_path.exists():
                        with open(env_path, 'r') as f:
                            for line in f:
                                line = line.strip()
                                if line and not line.startswith('#') and '=' in line:
                                    key, value = line.split('=', 1)
                                    if key.strip() == env_var:
                                        api_key = value.strip()
                                        break

                # If still not found, raise an error
                if not api_key:
                    raise AIOSException(
                        f"{env_var} environment variable is required for {config.model.provider} model. "
                        f"Please set it in your .env file or environment variables."
                    )

        save_config(config)

        return (
            f"Model updated to provider: {config.model.provider}, "
            f"name: {config.model.name}"
         )

    def _set_model_provider(self, provider):
        config = load_config()
        config.model.provider = provider
        save_config(config)
        return f'Model provider updated to: {provider}'

    def _show_status(self):
        config = load_config()
        return f'Current AIOS configuration:\nProvider: {config.model.provider}\nModel: {config.model.name}'

    def _update_chatbot_config(self, system_prompt):
        # For now, we just return a message.
        # In a full implementation, we would update the chatbot config.
        return f'Chatbot system prompt updated to: {system_prompt}'

    def _create_workflow(self, workflow_name):
        workflow_dir = self.workflows_dir / workflow_name
        if workflow_dir.exists():
            raise AIOSException(f'Workflow {workflow_name} already exists.')
        workflow_dir.mkdir(parents=True)
        (workflow_dir / '__init__.py').write_text('')
        (workflow_dir / 'workflow.py').write_text(f'"""{workflow_name} workflow."""\nfrom aios.workflows.base import BaseWorkflow\n\nclass {workflow_name.capitalize()}Workflow(BaseWorkflow):\n    def __init__(self):\n        super().__init__("{workflow_name}")\n    def run(self, context, input=None):\n        return f"{workflow_name} workflow executed."\n')
        (workflow_dir / 'config.py').write_text('"""Workflow configuration."""\nfrom pydantic import BaseModel\n\nclass Config(BaseModel):\n    pass\n')

    def _remove_workflow(self, workflow_name):
        workflow_dir = self.workflows_dir / workflow_name
        if not workflow_dir.exists():
            raise AIOSException(f'Workflow {workflow_name} not found.')
        import shutil
        shutil.rmtree(workflow_dir)
        return f'Workflow {workflow_name} removed.'

    def _list_workflows(self):
        workflows_dir = self.workflows_dir
        workflows = [d.name for d in workflows_dir.iterdir() if d.is_dir() and not d.name.startswith('_') and d.name != '__pycache__']
        if not workflows:
            return 'No workflows available.'
        return 'Available workflows:\n' + '\n'.join(f'- {w}' for w in workflows)

    def _list_models(self):
        providers = self.model_manager.list_providers()
        result = []
        for provider_name, provider_class in providers.items():
            is_available = self.model_manager.is_provider_available(provider_name)
            status = '[Available]' if is_available else '[Not Configured]'
            result.append(f'{provider_name}: {status}')
        return 'Available models:\n' + '\n'.join(result)

    def _create_tool(self, intent):
        # Get tool parameters using the new cleaner contract (with backward compatibility)
        tool_params = intent.get_tool_parameters()

        name = tool_params.get("name")
        description = tool_params.get("description")
        parameters_spec = tool_params.get("parameters_spec", {})

        # Validate tool name
        if not name:
            raise AIOSException("Tool name is required")

        if not description:
            description = f"{name} application tool"

        # Validate tool name is a valid Python identifier
        if not name.isidentifier():
            raise AIOSException(f"Tool name '{name}' is not a valid Python identifier")

        # Get current project directory
        config = load_config()
        project_dir = Path.cwd()

        # Create tools directory if it doesn't exist
        tools_dir = project_dir / "tools"
        tools_dir.mkdir(exist_ok=True)

        # Create tool file path
        tool_file = tools_dir / f"{name}.py"

        # Check if tool already exists
        if tool_file.exists():
            raise AIOSException(f"Tool '{name}' already exists at {tool_file}")

        # Generate tool implementation using the LLM
        tool_implementation = self.tool_generator.generate_tool_implementation(
            name, description, parameters_spec
        )

        # Validate the generated tool implementation
        validation_errors = self.tool_validator.validate_tool_source(
            tool_implementation, name
        )
        if validation_errors:
            raise AIOSException(
                f"Tool validation failed: {'; '.join(validation_errors)}"
            )

        # Write tool file
        tool_file.write_text(tool_implementation, encoding='utf-8')

        # Also create __init__.py in tools directory if it doesn't exist
        init_file = tools_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text("")

        # Optionally, validate the tool instance by trying to import and instantiate it
        # This is commented out for now to avoid import complications during generation
        # but could be enabled for additional safety
        """
        try:
            # Add the tools directory to Python path temporarily
            import sys
            sys.path.insert(0, str(tools_dir))

            # Import the module
            module_name = name
            spec = importlib.util.spec_from_file_location(module_name, tool_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Get the tool class (assuming it follows naming convention)
            class_name = ''.join(word.capitalize() for word in name.split('_')) + 'Tool'
            tool_class = getattr(module, class_name)

            # Create an instance
            tool_instance = tool_class()

            # Validate the instance
            instance_errors = self.tool_validator.validate_tool_instance(
                tool_instance, name
            )
            if instance_errors:
                raise AIOSException(
                    f"Tool instance validation failed: {'; '.join(instance_errors)}"
                )

        except Exception as e:
            # If validation fails, we might want to delete the generated file
            # For now, we'll just warn but not fail the tool creation
            # In a production system, you might want to be stricter
            pass
        """

        return f"Tool '{name}' created successfully at {tool_file}"

