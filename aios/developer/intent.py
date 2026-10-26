
from enum import Enum
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any


class DeveloperAction(str, Enum):
    SET_MODEL = 'set_model'
    SET_MODEL_PROVIDER = 'set_model_provider'
    SHOW_STATUS = 'show_status'
    UPDATE_CHATBOT_CONFIG = 'update_chatbot_config'
    CREATE_WORKFLOW = 'create_workflow'
    REMOVE_WORKFLOW = 'remove_workflow'
    LIST_WORKFLOWS = 'list_workflows'
    LIST_MODELS = 'list_models'
    CREATE_TOOL = 'create_tool'
    CLARIFICATION_REQUIRED = 'clarification_required'


class DeveloperIntent(BaseModel):
    action: DeveloperAction
    provider: Optional[str] = None
    model: Optional[str] = None
    workflow_name: Optional[str] = None
    system_prompt: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    # Fields for create_tool action (maintained for backward compatibility)
    name: Optional[str] = None
    description: Optional[str] = None
    parameters_spec: Optional[Dict[str, Any]] = None
    # Fields for clarification_required action
    question: Optional[str] = None

    @validator('parameters', pre=True, always=True)
    def default_parameters(cls, v):
        return v or {}

    def get_tool_parameters(self) -> Dict[str, Any]:
        """
        Get tool parameters, prioritizing the parameters field for new format,
        falling back to top-level fields for backward compatibility.
        """
        # If we have a parameters dict with tool info, use that (new format)
        if self.parameters and isinstance(self.parameters, dict):
            # Check if it contains tool-specific fields
            if any(key in self.parameters for key in ['name', 'description', 'parameters_spec']):
                return self.parameters

        # Otherwise, construct from top-level fields (backward compatibility)
        tool_params = {}
        if self.name is not None:
            tool_params['name'] = self.name
        if self.description is not None:
            tool_params['description'] = self.description
        if self.parameters_spec is not None:
            tool_params['parameters_spec'] = self.parameters_spec

        return tool_params

