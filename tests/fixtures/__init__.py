"""
Shared test fixtures for RapidKit tests

This module provides reusable fixtures that can be used across
different test modules to reduce duplication and ensure consistency.
"""

import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Generator

import pytest

if TYPE_CHECKING:
    from typer.testing import CliRunner


@pytest.fixture
def temp_project_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for project testing"""
    temp_dir = Path(tempfile.mkdtemp())
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """Sample project configuration for testing"""
    return {
        "name": "test_project",
        "version": "1.0.0",
        "description": "Test project",
        "dependencies": ["fastapi", "uvicorn"],
        "dev-dependencies": ["pytest", "black", "ruff"],
    }


@pytest.fixture
def sample_module_config() -> Dict[str, Any]:
    """Sample module configuration"""
    return {
        "name": "test_module",
        "type": "database",
        "config": {"database_url": "sqlite:///test.db", "migrations_dir": "migrations"},
    }


@pytest.fixture
def mock_cli_runner() -> "CliRunner":
    """Mock CLI runner for testing CLI commands"""
    from typer.testing import CliRunner

    return CliRunner()


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Directory containing test data files"""
    return Path(__file__).parent.parent / "data"


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    """Clean environment variables for testing"""
    # Remove any existing environment variables that might interfere
    env_vars_to_clean = ["RAPIDKIT_CONFIG", "RAPIDKIT_ENV", "PYTHONPATH"]

    for var in env_vars_to_clean:
        monkeypatch.delenv(var, raising=False)

    return monkeypatch


@pytest.fixture
def isolated_filesystem() -> Generator[Path, None, None]:
    """Run test in isolated filesystem"""
    original_cwd = Path.cwd()
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        # Change to temp directory
        import os

        os.chdir(temp_path)

        try:
            yield temp_path
        finally:
            # Restore original directory
            os.chdir(original_cwd)
