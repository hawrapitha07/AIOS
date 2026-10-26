"""
Tests for AIOS CLI.
"""

import pytest
from typer.testing import CliRunner
from aios.cli import app

runner = CliRunner()


def test_cli_help():
    """Test that CLI help works."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "AIOS" in result.output
    assert "AI Application Development Operating Environment" in result.output


def test_workflow_list():
    """Test workflow list command."""
    result = runner.invoke(app, ["workflow", "list"])
    assert result.exit_code == 0
    assert "Available Workflows" in result.output
    assert "chatbot" in result.output


def test_model_list():
    """Test model list command."""
    result = runner.invoke(app, ["model", "list"])
    assert result.exit_code == 0
    assert "Available Model Providers" in result.output
    assert "mock" in result.output


def test_status_command():
    """Test status command."""
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "AIOS Status" in result.output
    assert "Project:" in result.output
    assert "Model:" in result.output
    assert "Available Workflows" in result.output


def test_create_command():
    """Test project create command (basic test)."""
    # We'll test this in a temporary directory to avoid polluting the workspace
    result = runner.invoke(app, ["create", "--help"])
    assert result.exit_code == 0
    assert "Create a new AIOS project" in result.output