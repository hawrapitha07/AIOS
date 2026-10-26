import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch

from aios.developer.agent import DeveloperAgent
from aios.core.exceptions import AIOSException
from aios.managers.model_manager import ModelManager


def test_get_model_finds_aios_yaml_in_current_directory(monkeypatch):
    original_dir = Path.cwd()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        aios_yaml = tmpdir / "aios.yaml"
        aios_yaml.write_text(
            "model:\n"
            "  provider: mock\n"
            "  name: test\n"
        )

        monkeypatch.chdir(tmpdir)

        # Debug: check if file exists and what's in it
        print(f"Current directory: {Path.cwd()}")
        print(f"AIOS YAML path: {aios_yaml}")
        print(f"AIOS YAML exists: {aios_yaml.exists()}")
        if aios_yaml.exists():
            print(f"AIOS YAML content: {aios_yaml.read_text()}")

        def mock_create_model(provider, name, **kwargs):
            class DummyModel:
                def __init__(self, provider, name):
                    self.provider = provider
                    self.name = name

            return DummyModel(provider, name)

        with patch.object(
            ModelManager,
            "create_model",
            side_effect=mock_create_model
        ):
            agent = DeveloperAgent()
            model = agent._get_model()

            # Debug: print what we got
            print(f"Model provider: {model.provider}")
            print(f"Model name: {model.name}")

            assert model.provider == "mock"
            assert model.name == "test"

        monkeypatch.chdir(original_dir)


def test_get_model_finds_aios_yaml_in_parent_directory(monkeypatch):
    original_dir = Path.cwd()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        aios_yaml = tmpdir / "aios.yaml"
        aios_yaml.write_text(
            "model:\n"
            "  provider: mock\n"
            "  name: test\n"
        )

        subdir = tmpdir / "sub"
        subdir.mkdir()

        monkeypatch.chdir(subdir)

        def mock_create_model(provider, name, **kwargs):
            class DummyModel:
                def __init__(self, provider, name):
                    self.provider = provider
                    self.name = name

            return DummyModel(provider, name)

        with patch.object(
            ModelManager,
            "create_model",
            side_effect=mock_create_model
        ):
            agent = DeveloperAgent()
            model = agent._get_model()

            assert model.provider == "mock"
            assert model.name == "test"

        monkeypatch.chdir(original_dir)


def test_get_model_raises_when_no_aios_yaml(monkeypatch):
    original_dir = Path.cwd()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        subdir = tmpdir / "sub"
        subdir.mkdir()

        monkeypatch.chdir(subdir)

        agent = DeveloperAgent()

        with pytest.raises(
            AIOSException,
            match="No AIOS project found"
        ):
            agent._get_model()

        monkeypatch.chdir(original_dir)