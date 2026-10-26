"""
Chatbot workflow implementation for AIOS platform.
"""

from typing import Any, Optional, Dict, List
import time
from ..base import BaseWorkflow
from .config import ChatbotWorkflowConfig
from ...runtime.context import RuntimeContext
from ...models.base import Message


class ChatbotWorkflow(BaseWorkflow):
    """Chatbot workflow for AIOS platform."""

    def __init__(self, name: str = "chatbot", description: str = "AIOS Chatbot Workflow"):
        """
        Initialize the chatbot workflow.

        Args:
            name: Name of the workflow.
            description: Description of the workflow.
        """
        super().__init__(name, description)
        self.config = ChatbotWorkflowConfig()

    def run(self, input_data: Any, context: Optional[RuntimeContext] = None) -> Any:
        """
        Execute the chatbot workflow.

        Args:
            input_data: Input data (not used for chatbot, kept for interface consistency).
            context: Optional runtime context.

        Returns:
            Any: Workflow output (None for chatbot as it runs interactively).
        """
        # This method is kept for interface compliance but the actual
        # interactive chatbot is handled by the CLI command
        return None

    def start_interactive_session(self, context: RuntimeContext) -> None:
        """
        Start an interactive chatbot session.

        Args:
            context: Runtime context containing model manager and other services.
        """
        # Import here to avoid circular imports
        from rich.console import Console
        from rich.prompt import Prompt

        console = Console()

        # Get model from context
        model_provider = context.get_metadata("model_provider", "mock")
        model_name = context.get_metadata("model_name", "default")

        try:
            model = context.model_manager.get_model(model_provider, model_name)
            if model is None:
                # Create model if not cached
                model = context.model_manager.create_model(model_provider, model_name)
        except Exception as e:
            console.print(f"[red]Error initializing model: {e}[/red]")
            console.print("[yellow]Falling back to mock model[/yellow]")
            model = context.model_manager.create_model("mock", "default")

        # Display welcome message
        console.print("[bold blue]AIOS Chatbot[/bold blue]")
        console.print(f"Provider: [green]{model_provider}[/green] | Model: [green]{model_name}[/green]")
        console.print("Type 'exit' to quit.\n")

        # Add system message to conversation history
        system_message = self.config.system_prompt
        context.add_message("system", system_message)

        # Main chat loop
        while True:
            try:
                # Get user input
                user_input = Prompt.ask("[bold green]You[/bold green]")

                # Check for exit commands
                if user_input.lower() in [cmd.lower() for cmd in self.config.exit_commands]:
                    console.print("[yellow]Goodbye![/yellow]")
                    break

                # Add user message to history
                context.add_message("user", user_input)

                # Search knowledge sources for relevant context
                knowledge_results = context.search_knowledge_sources(user_input, top_k=3)

                # Get conversation history for model input
                conversation_history = context.get_conversation_history()

                # Limit history size
                if len(conversation_history) > self.config.max_history * 2 + 1:  # *2 for user/assistant pairs, +1 for system
                    # Keep system message and recent exchanges
                    system_msgs = [msg for msg in conversation_history if msg.role == "system"]
                    recent_msgs = conversation_history[-(self.config.max_history * 2):]
                    conversation_history = system_msgs + recent_msgs
                    # Update context history
                    context.conversation_history = conversation_history

                # If we have knowledge results, add them as context to the conversation
                if knowledge_results:
                    knowledge_context = (
                        "You are an AI assistant with access to a project knowledge base.\n"
                        "Use the knowledge base when it is relevant to the user's question.\n"
                        "If the knowledge base contains information that answers the question, "
                        "use that information as the primary source.\n"
                        "If the knowledge base does not contain relevant information, "
                        "answer the question using your general knowledge.\n\n"
                        "KNOWLEDGE BASE:\n"
                    )

                    for i, result in enumerate(knowledge_results, 1):
                     knowledge_context += f"{i}. {result['content']}\n"

                    knowledge_context += (
                        "\nEnd of knowledge base.\n"
                    )

                    last_user_index = -1
                    for i in range(len(conversation_history) - 1, -1, -1):
                        if conversation_history[i].role == "user":
                         last_user_index = i
                         break

                    if last_user_index != -1:
                        knowledge_message = Message(
                         role="system",
                         content=knowledge_context
                        )
                        conversation_history.insert(last_user_index, knowledge_message)

                # Generate response from model
                with console.status("[bold blue]AIOS is thinking...[/bold blue]"):
                    try:
                        response = model.generate(
                            messages=conversation_history,
                            temperature=0.7
                        )
                    except Exception as e:
                        response = f"Error generating response: {str(e)}"

                # Add assistant message to history
                context.add_message("assistant", response)

                # Display response
                console.print(f"[bold blue]AIOS:[/bold blue] {response}\n")

            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]")
                continue
            except EOFError:
                console.print("\n[yellow]Goodbye![/yellow]")
                break