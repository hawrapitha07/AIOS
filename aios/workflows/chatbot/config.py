"""
Configuration for chatbot workflow.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class ChatbotWorkflowConfig(BaseModel):
    """Configuration for chatbot workflow."""
    system_prompt: str = Field(
        default="You are a helpful AI assistant.",
        description="System prompt for the chatbot"
    )
    max_history: int = Field(
        default=10,
        description="Maximum number of conversation turns to keep in history"
    )
    exit_commands: List[str] = Field(
        default=["exit", "quit", "bye"],
        description="Commands to exit the chatbot"
    )