"""
AIOS Command Line Interface.
"""

import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
import os
from pathlib import Path

from aios.core.config import load_config, save_config, AIOSConfig
from aios.managers.project_manager import ProjectManager
from aios.managers.model_manager import ModelManager
from aios.managers.workflow_manager import WorkflowManager
from aios.runtime.agent import AgentRuntime
from aios.workflows.chatbot.workflow import ChatbotWorkflow
from aios.core.exceptions import (
    AIOSException,
    WorkflowNotFoundError,
    ModelProviderError,
    ProjectError
)

from aios.developer.agent import DeveloperAgent
app = typer.Typer(
    name="aios",
    help="AIOS - AI Application Development Operating Environment",
    add_completion=False,
)
console = Console()


def setup_chatbot(project_dir: Path):
    """Guided setup for chatbot workflow."""
    # Change to the project directory for subsequent operations
    try:
        os.chdir(project_dir)
    except Exception as e:
        console.print(f"[yellow]Warning: Could not change to project directory: {e}[/yellow]")
        console.print("Continuing in current directory...")

    # Initialize managers for guided setup
    try:
        model_manager = ModelManager()
    except Exception as e:
        console.print(f"[yellow]Warning: Could not initialize model manager: {e}[/yellow]")
        console.print("Some features may not be available.")

    # Guided chatbot setup
    console.print("\n[bold blue]AIOS Chatbot Setup[/bold blue]")
    console.print("Let's configure your chatbot application.\n")

    # Note: The project name is already set in the config, but we can show it again
    # We'll load the config to show the project name
    try:
        config = load_config()
        project_name = config.name
        console.print(f"Project name: {project_name}\n")
    except Exception as e:
        console.print(f"[yellow]Warning: Could not load config: {e}[/yellow]")
        console.print("Project name: [unknown]\n")

    # Helper function to find project root
    def _find_project_root() -> Path:
        """Find the project root by looking for aios.yaml in current directory or parent directories."""
        current = Path.cwd()
        while current != current.parent:
            if (current / "aios.yaml").exists():
                return current
            current = current.parent
        return Path.cwd()  # Fallback to current directory if not found

    # Step 1: Model configuration
    console.print("[bold]Step 1: Model Configuration[/bold]")
    console.print("How would you like to use the AI model?")
    console.print("1. Local model")
    console.print("2. Cloud/API model")
    console.print("3. Configure later")

    model_choice = typer.prompt(
        "Choose [1/2/3]",
        default="3"
    )

    provider = None
    model_name = None

    if model_choice == "1":
        # Local model selected
        console.print("\nEnter your local model provider:")
        provider_input = typer.prompt("> ")
        provider = provider_input.lower().strip()

        console.print("\nEnter your local model name:")
        model_name_input = typer.prompt("> ")
        model_name = model_name_input.strip()

        # Show recommendation
        console.print("\n[dim]Recommended local setup:[/dim]")
        console.print("Provider: Ollama")
        console.print("Model: llama3.2:3b")

    elif model_choice == "2":
        # Cloud/API model selected
        console.print("\nEnter your API model provider:")
        provider_input = typer.prompt("> ")
        provider = provider_input.lower().strip()

        console.print("\nEnter your model name:")
        model_name_input = typer.prompt("> ")
        model_name = model_name_input.strip()

        # Determine the appropriate environment variable name for the provider
        env_var_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_API_KEY"
        }

        env_var = env_var_map.get(provider)
        if env_var is None:
            # For unsupported providers, we'll ask the user to specify the env var
            console.print(f"\n[yellow]Warning: Provider '{provider}' is not in the predefined list.[/yellow]")
            console.print("You'll need to set the appropriate API key environment variable in your .env file.")
            console.print("Check your provider's documentation for the correct environment variable name.")

            # Ask if they want to specify the environment variable name
            try:
                specify_env_var = typer.confirm("Do you want to specify the environment variable name for this provider?", default=False)
                if specify_env_var:
                    env_var_input = typer.prompt("Enter the environment variable name (e.g., OPENAI_API_KEY): ")
                    env_var = env_var_input.strip().upper()
                    if not env_var:
                        console.print("[yellow]No environment variable specified. You'll need to set it manually in .env file.[/yellow]")
                        env_var = None
            except Exception:
                console.print("[yellow]Could not process environment variable input. You'll need to set it manually in .env file.[/yellow]")
                env_var = None

        if env_var is not None:
            console.print(f"\nFor {provider_input}, set {env_var} in your .env file.")

        # Ask for API key
        console.print(f"\nEnter your {provider_input} API key:")
        api_key = typer.prompt("", password=True)  # Hide input

        # Save API key to .env file
        if api_key:
            try:
                env_path = project_dir / ".env"
                # Read existing .env file if it exists
                env_vars = {}
                if env_path.exists():
                    with open(env_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and '=' in line:
                                key, value = line.split('=', 1)
                                env_vars[key.strip()] = value.strip()

                # Add/update the API key
                env_vars[env_var] = api_key

                # Write back to .env file
                with open(env_path, 'w') as f:
                    for key, value in env_vars.items():
                        f.write(f"{key}={value}\n")

                console.print(f"[green][+][/green] API key saved to .env file as {env_var}")
            except Exception as e:
                console.print(f"[red]Error saving API key to .env file: {e}[/red]")
                raise typer.Exit(1)
        else:
            console.print("[yellow]No API key provided. You'll need to set it manually in .env file.[/yellow]")

    elif model_choice == "3":
        # Configure later - keep default (mock)
        console.print("[yellow]Model configuration skipped. Will use default (mock) model.[/yellow]")
        console.print("You can configure the model later using 'aios ask \"switch my model to ...\"'")
    else:
        # Invalid choice, default to configure later
        console.print("[yellow]Invalid choice, skipping model configuration.[/yellow]")
        console.print("You can configure the model later using 'aios ask \"switch my model to ...\"'")

    # Update the configuration with the selected model (if any)
    if provider is not None and model_name is not None:
        try:
            config = load_config()
            config.model.provider = provider
            config.model.name = model_name
            save_config(config)
            console.print(f"\n[green][+][/green] Model configured: {provider}:{model_name}")
        except Exception as e:
            console.print(f"[red]Error saving model configuration: {e}[/red]")
            raise typer.Exit(1)
    else:
        # No model selected, keep existing config (likely mock)
        console.print("\n[yellow]Model configuration skipped.[/yellow]")

    # Step 2: Knowledge base setup
    console.print("\n[bold]Step 2: Knowledge Base Setup[/bold]")
    add_knowledge = typer.prompt(
        "Do you want to add a knowledge base now?",
        default="no"
    )
    # Validate knowledge base choice
    add_knowledge = add_knowledge.lower()
    if add_knowledge not in ["yes", "no"]:
        console.print("[red]Error:[/red] Invalid choice. Please choose 'yes' or 'no'.")
        raise typer.Exit(1)

    if add_knowledge.lower() == "yes":
        knowledge_path = typer.prompt(
            "Enter the path to your knowledge file",
            default="knowledge/company_docs.txt"
        )

        # Validate the file exists
        knowledge_file = Path(knowledge_path)
        if not knowledge_file.exists():
            console.print(f"[yellow]Warning: File '{knowledge_path}' not found.[/yellow]")
            console.print("You can add it later using 'aios knowledge add <path>'")
        else:
            # Update the configuration to include this knowledge source
            try:
                config = load_config()
                if not hasattr(config, 'knowledge') or config.knowledge is None:
                    from aios.core.config import KnowledgeConfig
                    config.knowledge = KnowledgeConfig()

                # Check if we already have knowledge sources
                if not config.knowledge.sources:
                    config.knowledge.sources = []

                # Determine if the file is inside the project
                project_root = _find_project_root()
                abs_knowledge_file = knowledge_file.absolute()
                try:
                    # If the file is inside the project, store a relative path
                    relative_path = abs_knowledge_file.relative_to(project_root)
                    storage_path = str(relative_path)
                except ValueError:
                    # If the file is outside the project, store the absolute path
                    storage_path = str(abs_knowledge_file)

                # Add the knowledge source
                from aios.core.config import DocumentKnowledgeConfig
                knowledge_source = DocumentKnowledgeConfig(
                    name=knowledge_file.stem,
                    type="document",
                    path=storage_path
                )
                config.knowledge.sources.append(knowledge_source)
                save_config(config)

                console.print(f"[green][+][/green] Knowledge source added: {knowledge_path}")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not save knowledge configuration: {e}[/yellow]")

    # Step 3: Tools setup
    console.print("\n[bold]Step 3: Tools Setup[/bold]")
    console.print("[dim]Tools can be added later using 'aios ask \"create a <tool> tool\"'[/dim]")

    # Create the chatbot workflow configuration
    console.print("\n[bold]Step 4: Workflow Configuration[/bold]")
    console.print("[green][+][/green] Chatbot workflow configured")

    # Final summary
    console.print("\n[bold green]Chatbot created successfully![/bold green]")
    console.print(f"\nProject: {config.name if 'config' in locals() else 'unknown'}")
    console.print(f"\nModel:")
    # Reload config to get the current values
    config = load_config()
    console.print(f"  Provider: {config.model.provider}")
    console.print(f"  Model: {config.model.name}")

    # Show knowledge sources if any
    try:
        config = load_config()
        if hasattr(config, 'knowledge') and config.knowledge.sources:
            console.print(f"\nKnowledge:")
            for source in config.knowledge.sources:
                console.print(f"  {source.name} ({source.type}): {source.path}")
        else:
            console.print(f"\nKnowledge: None")
    except Exception as e:
        console.print(f"[yellow]Warning: Could not load configuration for summary: {e}[/yellow]")
        console.print(f"\nKnowledge: None (error loading config)")

    console.print(f"\nTools: None")
    console.print(f"\nWorkflow:")
    console.print(f"  chatbot")

    console.print(f"\n[bold]Next steps:[/bold]")
    console.print(f"  1. Review and edit aios.yaml if needed")
    console.print(f"  2. pip install -e .")
    console.print(f"  3. aios workflow run chatbot")
    console.print(f"  4. aios knowledge add <file>  # To add knowledge sources")
    console.print(f"  5. aios ask \"create a <tool> tool\"  # To create tools")
    console.print(f"  6. aios ask \"switch my model to ...\"  # To change models")


@app.command()
def create(
    workflow_type: str = typer.Argument(..., help="Type of workflow to create (e.g., chatbot, incident-investigator)"),
    project_name: str = typer.Argument(..., help="Name of the project to create"),
    directory: Optional[str] = typer.Option(None, "--dir", "-d", help="Directory to create the project in")
):
    """Create a new AIOS project."""
    try:
        # First, check if the workflow exists
        workflow_manager = WorkflowManager()
        # Register the chatbot workflow (and any other workflows we know about)
        chatbot_workflow = ChatbotWorkflow()
        workflow_manager.register_workflow(chatbot_workflow)
        # Note: In the future, we might register other workflows here or via a plugin system.
        if not workflow_manager.workflow_exists(workflow_type):
            available_workflows = list(workflow_manager.list_workflows().keys())
            console.print(f"[red]Error:[/red] Unknown workflow: {workflow_type}")
            if available_workflows:
                console.print("[dim]Available workflows:[/dim]")
                for wf in available_workflows:
                    console.print(f"  - {wf}")
            else:
                console.print("[dim]No workflows registered.[/dim]")
            raise typer.Exit(1)

        # Create the project structure
        project_manager = ProjectManager()
        project_dir = project_manager.create_project(project_name, directory)

        console.print(f"[green][+][/green] Created project structure at: [blue]{project_dir}[/blue]")

        # If the workflow is chatbot, run the guided setup
        if workflow_type == "chatbot":
            setup_chatbot(project_dir)
        else:
            # For other workflows, just create the generic project
            console.print(f"[green][+][/green] Project '{project_name}' created successfully at: [blue]{project_dir}[/blue]")
            console.print("\n[dim]Next steps:[/dim]")
            console.print(f"  1. cd {project_dir}")
            console.print("  2. pip install -e .")
            console.print("  3. aios workflow run chatbot  # Note: only chatbot workflow is available for now")

    except ProjectError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {type(e).__name__}: {e}")
        raise typer.Exit(1)


@app.command()
def workflow(
    action: str = typer.Argument(..., help="Action to perform (list, run)"),
    name: Optional[str] = typer.Argument(None, help="Workflow name (for run action)")
):
    """Manage AIOS workflows."""
    if action == "list":
        _list_workflows()
    elif action == "run":
        if name is None:
            console.print("[red]Error:[/red] Workflow name required for 'run' action")
            raise typer.Exit(1)
        _run_workflow(name)
    else:
        console.print(f"[red]Error:[/red] Unknown action '{action}'. Use 'list' or 'run'.")
        raise typer.Exit(1)


@app.command()
def model(
    action: str = typer.Argument(..., help="Action to perform (list)"),
):
    """Manage AIOS models."""
    if action == "list":
        _list_models()
    else:
        console.print(f"[red]Error:[/red] Unknown action '{action}'. Use 'list'.")
        raise typer.Exit(1)


@app.command()
def tool(
    action: str = typer.Argument(..., help="Action to perform (list)")
):
    """Manage AIOS application tools."""
    if action == "list":
        _list_tools()
    else:
        console.print(
            f"[red]Error:[/red] Unknown action '{action}'. Use 'list'."
        )
        raise typer.Exit(1)


@app.command()
def knowledge(
    action: str = typer.Argument(..., help="Action to perform (list, add)"),
    path: Optional[str] = typer.Argument(None, help="Path to knowledge file (for add action)")
):
    """Manage AIOS knowledge base."""
    if action == "list":
        _list_knowledge()
    elif action == "add":
        if path is None:
            console.print("[red]Error:[/red] Path required for 'add' action")
            raise typer.Exit(1)
        _add_knowledge(path)
    else:
        console.print(
            f"[red]Error:[/red] Unknown action '{action}'. Use 'list' or 'add'."
        )
        raise typer.Exit(1)


@app.command()
def create_chatbot(
    project_name: str = typer.Argument(..., help="Name of the chatbot project"),
    directory: Optional[str] = typer.Option(None, "--dir", "-d", help="Directory to create the project in")
):
    """Create a new AIOS chatbot project with guided setup."""
    console.print("[yellow]Warning: This command is deprecated. Use 'aios create chatbot <project_name>' instead.[/yellow]")
    # Delegate to the new create command
    try:
        # We'll create the project and then run the chatbot setup
        project_manager = ProjectManager()
        project_dir = project_manager.create_project(project_name, directory)
        console.print(f"[green][+][/green] Created project structure at: [blue]{project_dir}[/blue]")
        setup_chatbot(project_dir)
    except Exception as e:
        console.print(f"[red]Error creating chatbot:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def status():
    """Show AIOS status."""
    _show_status()


@app.command()
def ask(
    request: str = typer.Argument(..., help="Natural language request for the Developer Agent")
):
    """Ask the Developer Agent to perform a task."""
    try:
        developer_agent = DeveloperAgent()
        result = developer_agent.execute_request(request)
        console.print(result)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def _list_workflows():
    """List available workflows."""
    try:
        # Initialize workflow manager and register chatbot workflow
        workflow_manager = WorkflowManager()
        chatbot_workflow = ChatbotWorkflow()
        workflow_manager.register_workflow(chatbot_workflow)

        workflows = workflow_manager.list_workflows()

        console.print("\n[bold]Available Workflows:[/bold]")
        if not workflows:
            console.print("[dim]No workflows registered[/dim]")
            return

        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="white")

        for name, workflow in workflows.items():
            table.add_row(name, workflow.description or "No description")

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error listing workflows:[/red] {e}")
        raise typer.Exit(1)


def _run_workflow(workflow_name: str):
    """Run a specific workflow."""
    try:
        # Initialize managers
        model_manager = ModelManager()
        workflow_manager = WorkflowManager()
        from aios.knowledge.manager import KnowledgeManager
        knowledge_manager = KnowledgeManager()
        agent_runtime = AgentRuntime(model_manager, workflow_manager)

        # Register chatbot workflow
        chatbot_workflow = ChatbotWorkflow()
        workflow_manager.register_workflow(chatbot_workflow)

        # Check if workflow exists
        if not workflow_manager.workflow_exists(workflow_name):
            available = list(workflow_manager.list_workflows().keys())
            console.print(f"[red]Error:[/red] Workflow '{workflow_name}' not found.")
            console.print(f"[dim]Available workflows: {', '.join(available)}[/dim]")
            raise typer.Exit(1)

        # Create runtime context
        context = agent_runtime.create_context()

        # Load configuration to get model settings
        config = load_config()
        context.set_metadata("model_provider", config.model.provider)
        context.set_metadata("model_name", config.model.name)

        # Load knowledge sources from configuration
        if hasattr(config, 'knowledge') and config.knowledge.sources:
            knowledge_manager.load_from_config(config.knowledge, Path.cwd())
            context.set_knowledge_manager(knowledge_manager)

        # For chatbot workflow, start interactive session
        if workflow_name == "chatbot":
            chatbot_workflow.start_interactive_session(context)
        else:
            # For other workflows, use the standard run method
            result = workflow_manager.run_workflow(workflow_name, None, context)
            console.print(f"[green]Workflow completed.[/green]")
            if result is not None:
                console.print(f"Result: {result}")

    except WorkflowNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except ModelProviderError as e:
        console.print(f"[red]Model Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error running workflow:[/red] {type(e).__name__}: {e}")
        raise typer.Exit(1)


def _list_models():
    """List available model providers."""
    try:
        model_manager = ModelManager()
        providers = model_manager.list_providers()

        console.print("\n[bold]Available Model Providers:[/bold]")
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Provider", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Description", style="white")

        for provider_name, provider_class in providers.items():
            # Check if provider is available
            is_available = model_manager.is_provider_available(provider_name)
            status = "[green]Available[/green]" if is_available else "[yellow]Not Configured[/yellow]"

            description = {
                "mock": "Mock model for testing and development",
                "openai": "OpenAI GPT models",
                "ollama": "Ollama local models"
            }.get(provider_name, "AI model provider")

            table.add_row(provider_name, status, description)

        console.print(table)
        console.print("\n[dim]Note: OpenAI provider requires OPENAI_API_KEY environment variable[/dim]")
    except Exception as e:
        console.print(f"[red]Error listing models:[/red] {type(e).__name__}: {e}")
        raise typer.Exit(1)


def _list_tools():
    """List tools generated in the current AIOS application."""
    try:
        tools_dir = Path.cwd() / "tools"

        console.print("\n[bold]Available Application Tools:[/bold]")

        if not tools_dir.exists():
            console.print("[dim]No tools directory found.[/dim]")
            return

        tool_files = [
            file for file in tools_dir.glob("*.py")
            if file.name != "__init__.py"
        ]

        if not tool_files:
            console.print("[dim]No tools available.[/dim]")
            return

        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Name", style="cyan")
        table.add_column("File", style="white")

        for tool_file in sorted(tool_files):
            table.add_row(
                tool_file.stem,
                str(tool_file)
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing tools:[/red] {type(e).__name__}: {e}")
        raise typer.Exit(1)


def _list_knowledge():
    """List knowledge sources in the current AIOS application."""
    try:
        # Load configuration
        config = load_config()

        console.print("\n[bold]Available Knowledge Sources:[/bold]")

        if not hasattr(config, 'knowledge') or not config.knowledge.sources:
            console.print("[dim]No knowledge sources configured.[/dim]")
            return

        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="white")
        table.add_column("Path", style="white")

        for source in config.knowledge.sources:
            table.add_row(
                source.name,
                source.type,
                source.path
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing knowledge:[/red] {type(e).__name__}: {e}")
        raise typer.Exit(1)


def _find_project_root() -> Path:
    """Find the project root by looking for aios.yaml in current directory or parent directories."""
    current = Path.cwd()
    while current != current.parent:
        if (current / "aios.yaml").exists():
            return current
        current = current.parent
    return Path.cwd()  # Fallback to current directory if not found


def _add_knowledge(path: str):
    """Add a knowledge source to the AIOS application."""
    try:
        # Load configuration
        config = load_config()

        # Validate the file exists
        knowledge_file = Path(path)
        if not knowledge_file.exists():
            console.print(f"[red]Error:[/red] File '{path}' not found.")
            raise typer.Exit(1)

        # Initialize knowledge configuration if needed
        if not hasattr(config, 'knowledge') or config.knowledge is None:
            from aios.core.config import KnowledgeConfig
            config.knowledge = KnowledgeConfig()

        # Check if we already have knowledge sources
        if not config.knowledge.sources:
            config.knowledge.sources = []

        # Check if this knowledge source already exists (by name)
        knowledge_name = knowledge_file.stem
        for source in config.knowledge.sources:
            if source.name == knowledge_name:
                console.print(f"[yellow]Warning:[/yellow] Knowledge source '{knowledge_name}' already exists.")
                # Ask if they want to overwrite
                if not typer.confirm("Do you want to overwrite it?", default=False):
                    console.print("Knowledge source not added.")
                    return
                # Remove the existing one
                config.knowledge.sources = [s for s in config.knowledge.sources if s.name != knowledge_name]
                break

        # Determine if the file is inside the project
        project_root = _find_project_root()
        abs_knowledge_file = knowledge_file.absolute()
        try:
            # If the file is inside the project, store a relative path
            relative_path = abs_knowledge_file.relative_to(project_root)
            storage_path = str(relative_path)
        except ValueError:
            # If the file is outside the project, store the absolute path
            storage_path = str(abs_knowledge_file)

        # Add the knowledge source
        from aios.core.config import DocumentKnowledgeConfig
        knowledge_source = DocumentKnowledgeConfig(
            name=knowledge_name,
            type="document",
            path=storage_path
        )
        config.knowledge.sources.append(knowledge_source)
        save_config(config)

        console.print(f"[green][+][/green] Knowledge source added: {path}")

    except Exception as e:
        console.print(f"[red]Error adding knowledge:[/red] {type(e).__name__}: {e}")
        raise typer.Exit(1)


def _show_status():
    """Show AIOS status."""
    try:
        # Load configuration
        config = load_config()

        # Initialize managers to get actual counts
        model_manager = ModelManager()
        workflow_manager = WorkflowManager()

        # Register chatbot workflow for counting
        chatbot_workflow = ChatbotWorkflow()
        workflow_manager.register_workflow(chatbot_workflow)

        # Get current directory info
        cwd = Path.cwd()
        aios_yaml = cwd / "aios.yaml"
        project_name = config.name if aios_yaml.exists() else "No AIOS project"

        console.print("\n[bold]AIOS Status[/bold]")
        console.print("=" * 50)

        # Project info
        project_panel = Panel(
            f"[cyan]Project:[/cyan] {project_name}\n"
            f"[cyan]Directory:[/cyan] {cwd}",
            title="Project",
            border_style="blue"
        )
        console.print(project_panel)

        # Model info
        model_panel = Panel(
            f"[cyan]Provider:[/cyan] {config.model.provider}\n"
            f"[cyan]Model:[/cyan] {config.model.name}\n"
            f"[cyan]Temperature:[/cyan] {config.model.temperature}",
            title="Model",
            border_style="green"
        )
        console.print(model_panel)

        # Workflow info
        workflows = workflow_manager.list_workflows()
        workflow_list = "\n".join([f"[green][+][/green] {name}" for name in workflows.keys()]) if workflows else "[dim]None[/dim]"
        workflow_panel = Panel(
            workflow_list,
            title="Available Workflows",
            border_style="yellow"
        )
        console.print(workflow_panel)

        # Counts
        # Count knowledge sources
        knowledge_count = 0
        if hasattr(config, 'knowledge') and config.knowledge.sources:
            knowledge_count = len(config.knowledge.sources)

        # Count tools
        tools_count = 0
        tools_dir = Path.cwd() / "tools"
        if tools_dir.exists():
            tool_files = [
                file for file in tools_dir.glob("*.py")
                if file.name != "__init__.py"
            ]
            tools_count = len(tool_files)

        counts_panel = Panel(
            f"[cyan]Knowledge Sources:[/cyan] {knowledge_count}\n"
            f"[cyan]Tools:[/cyan] {tools_count}",
            title="Resources",
            border_style="magenta"
        )
        console.print(counts_panel)

    except Exception as e:
        console.print(f"[red]Error showing status:[/red] {type(e).__name__}: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()