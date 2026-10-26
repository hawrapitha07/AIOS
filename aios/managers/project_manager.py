"""
Project manager for AIOS platform.
Handles creating new AIOS projects.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from ..core.exceptions import ProjectError
from ..core.config import AIOSConfig, save_config


class ProjectManager:
    """Manages AIOS project creation."""

    def __init__(self):
        """Initialize the project manager."""
        # Template directory relative to this file
        self.template_dir = Path(__file__).parent.parent.parent / "templates" / "project"

    def create_project(self, project_name: str, directory: Optional[str] = None) -> Path:
        """
        Create a new AIOS project.

        Args:
            project_name: Name of the project to create.
            directory: Directory to create the project in. If None, uses current directory.

        Returns:
            Path: Path to the created project directory.

        Raises:
            ProjectError: If project creation fails.
        """
        # Determine project directory
        if directory is None:
            project_dir = Path.cwd() / project_name
        else:
            project_dir = Path(directory) / project_name

        # Check if project directory already exists
        if project_dir.exists():
            raise ProjectError(f"Project directory '{project_dir}' already exists")

        try:
            # Create project directory structure
            self._create_project_structure(project_dir)

            # Create default configuration
            self._create_default_config(project_dir, project_name)

            # Create .gitignore
            self._create_gitignore(project_dir)

            # Create .env.example
            self._create_env_example(project_dir)

            return project_dir

        except Exception as e:
            # Clean up if creation failed
            if project_dir.exists():
                shutil.rmtree(project_dir)
            raise ProjectError(f"Failed to create project: {str(e)}")

    def _create_project_structure(self, project_dir: Path) -> None:
        """Create the basic project directory structure."""
        # Create directories
        dirs_to_create = [
            "models",
            "knowledge",
            "tools",
            "workflows",
            "app"
        ]

        for dir_name in dirs_to_create:
            (project_dir / dir_name).mkdir(parents=True, exist_ok=True)

        # Create __init__.py files
        init_files = [
            "models/__init__.py",
            "knowledge/__init__.py",
            "tools/__init__.py",
            "workflows/__init__.py",
            "app/__init__.py"
        ]

        for init_file in init_files:
            (project_dir / init_file).touch()

    def _create_default_config(self, project_dir: Path, project_name: str) -> None:
        """Create default aios.yaml configuration."""
        config = AIOSConfig(
            name=project_name,
            # Default to mock model for easy startup
        )

        config_path = project_dir / "aios.yaml"
        save_config(config, str(config_path))

    def _create_gitignore(self, project_dir: Path) -> None:
        """Create .gitignore file."""
        gitignore_content = """
# AIOS Specific
.aios/
.env
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
.venv/
venv/
ENV/
env.bak/
virtualenv/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Temporary files
*.tmp
*.temp
""".strip()

        (project_dir / ".gitignore").write_text(gitignore_content)

    def _create_env_example(self, project_dir: Path) -> None:
        """Create .env.example file."""
        env_example_content = """# AIOS Environment Variables
# Copy this file to .env and fill in your values

# OpenAI API Key (for OpenAI provider)
OPENAI_API_KEY=your_openai_api_key_here

# Ollama host (for Ollama provider, defaults to localhost:11434)
# OLLAMA_HOST=localhost:11434
""".strip()

        (project_dir / ".env.example").write_text(env_example_content)