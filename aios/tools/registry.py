"""
Tool registry for AIOS platform.
Handles discovery, loading, and validation of application tools.
"""

import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from aios.tools.validator import ToolValidator
from aios.tools.base import BaseTool
from aios.core.exceptions import AIOSException


class ToolRegistry:
    """Registry for discovering and managing application tools."""

    def __init__(self, project_dir: Optional[Path] = None):
        """
        Initialize the tool registry.

        Args:
            project_dir: Project directory to search for tools. If None, uses current directory.
        """
        self.project_dir = project_dir or Path.cwd()
        self.tools_dir = self.project_dir / "tools"
        self.validator = ToolValidator()
        self._loaded_tools: Dict[str, BaseTool] = {}
        self._tool_modules: Dict[str, Any] = {}  # Cache for loaded modules

    def discover_tools(self) -> List[str]:
        """
        Discover available tools in the tools directory.

        Returns:
            List[str]: List of tool names (without .py extension) that are discoverable.
        """
        if not self.tools_dir.exists():
            return []

        tool_files = [
            file for file in self.tools_dir.glob("*.py")
            if file.name != "__init__.py" and not file.name.startswith("_")
        ]

        return [file.stem for file in tool_files]

    def load_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        Load a specific tool by name.

        Args:
            tool_name: Name of the tool to load (without .py extension).

        Returns:
            BaseTool: Loaded tool instance, or None if loading fails.
        """
        # Return cached tool if already loaded
        if tool_name in self._loaded_tools:
            return self._loaded_tools[tool_name]

        # Check if tool exists
        tool_file = self.tools_dir / f"{tool_name}.py"
        if not tool_file.exists():
            return None

        try:
            # Load the module
            spec = importlib.util.spec_from_file_location(tool_name, tool_file)
            if spec is None or spec.loader is None:
                return None

            module = importlib.util.module_from_spec(spec)

            # Add the tools directory to sys.path to allow imports from within the tool
            tools_dir_str = str(self.tools_dir)
            if tools_dir_str not in sys.path:
                sys.path.insert(0, tools_dir_str)

            try:
                spec.loader.exec_module(module)
            finally:
                # Remove the tools directory from sys.path if we added it
                if tools_dir_str in sys.path:
                    sys.path.remove(tools_dir_str)

            # Find the tool class (should inherit from BaseTool)
            tool_class = None
            for item_name in dir(module):
                item = getattr(module, item_name)
                if (isinstance(item, type) and
                    issubclass(item, BaseTool) and
                    item != BaseTool):
                    tool_class = item
                    break

            if tool_class is None:
                return None

            # Create an instance
            tool_instance = tool_class()

            # Validate the tool instance
            validation_errors = self.validator.validate_tool_instance(
                tool_instance, tool_name
            )
            if validation_errors:
                raise AIOSException(
                    f"Tool validation failed for '{tool_name}': {'; '.join(validation_errors)}"
                )

            # Cache the loaded tool
            self._loaded_tools[tool_name] = tool_instance
            self._tool_modules[tool_name] = module

            return tool_instance

        except Exception:
            # If any error occurs during loading, return None
            return None

    def load_all_tools(self) -> Dict[str, BaseTool]:
        """
        Load all discoverable tools.

        Returns:
            Dict[str, BaseTool]: Dictionary of tool names to tool instances.
        """
        tool_names = self.discover_tools()
        loaded_tools = {}

        for tool_name in tool_names:
            tool = self.load_tool(tool_name)
            if tool is not None:
                loaded_tools[tool_name] = tool

        return loaded_tools

    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        Get a loaded tool by name.

        Args:
            tool_name: Name of the tool to retrieve.

        Returns:
            BaseTool: Tool instance if found and loaded, None otherwise.
        """
        # Try to get from cache first
        if tool_name in self._loaded_tools:
            return self._loaded_tools[tool_name]

        # Try to load it
        return self.load_tool(tool_name)

    def unload_tool(self, tool_name: str) -> bool:
        """
        Unload a tool from the registry.

        Args:
            tool_name: Name of the tool to unload.

        Returns:
            bool: True if tool was unloaded, False if not found.
        """
        if tool_name in self._loaded_tools:
            del self._loaded_tools[tool_name]
            if tool_name in self._tool_modules:
                del self._tool_modules[tool_name]
            return True
        return False

    def unload_all_tools(self) -> None:
        """Unload all tools from the registry."""
        self._loaded_tools.clear()
        self._tool_modules.clear()

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, str]]:
        """
        Get information about a tool.

        Args:
            tool_name: Name of the tool.

        Returns:
            Dict[str, str]: Tool information (name, description) or None if not found.
        """
        tool = self.get_tool(tool_name)
        if tool is not None:
            return tool.get_info()
        return None

    def list_available_tools(self) -> List[str]:
        """
        List all available tool names.

        Returns:
            List[str]: List of available tool names.
        """
        return self.discover_tools()

    def list_loaded_tools(self) -> List[str]:
        """
        List all currently loaded tool names.

        Returns:
            List[str]: List of loaded tool names.
        """
        return list(self._loaded_tools.keys())