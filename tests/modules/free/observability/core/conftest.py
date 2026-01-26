"""Shared fixtures for observability_core module tests."""

from pathlib import Path

import pytest

from modules.free.observability.core import generate


@pytest.fixture()
def module_root() -> Path:
    """Return the module root path for observability_core."""
    return Path(generate.MODULE_ROOT)
