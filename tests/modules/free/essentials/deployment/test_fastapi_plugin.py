# ruff: noqa: I001, SLF001
"""Deployment FastAPI plugin behaviour tests."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest  # type: ignore[import-not-found]

from modules.free.essentials.deployment.frameworks.fastapi import FastAPIPlugin


def test_fastapi_context_enrichments_include_defaults() -> None:
    plugin = FastAPIPlugin()
    base_context: dict[str, Any] = {"project_name": "demo"}

    context = plugin.get_context_enrichments(base_context)

    assert context["framework"] == "fastapi"
    assert context["framework_display_name"] == "FastAPI"
    assert context["language"] == "python"
    assert context["runtime"] == "python"
    assert context["include_ci"] is True
    assert context["include_postgres"] is True
    assert context["python_version"] == "3.10.14"


def test_fastapi_dependencies_lists_expected_packages() -> None:
    plugin = FastAPIPlugin()

    assert "fastapi>=0.119.0" in plugin.get_dependencies()
    dev_deps = plugin.get_dev_dependencies()
    assert "pytest-asyncio>=0.23.0" in dev_deps
    assert "httpx>=0.28.0" in dev_deps


def test_fastapi_pre_generation_creates_required_directories(tmp_path: Path) -> None:
    plugin = FastAPIPlugin()

    plugin.pre_generation_hook(tmp_path)

    assert (tmp_path / ".github" / "workflows").exists()


def test_fastapi_validate_requirements_handles_missing_package(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plugin = FastAPIPlugin()

    monkeypatch.delitem(sys.modules, "fastapi", raising=False)
    monkeypatch.setattr(
        "modules.free.essentials.deployment.frameworks.fastapi.importlib.util.find_spec",
        lambda _: None,
    )

    assert plugin.validate_requirements() == []


def test_fastapi_validate_requirements_uses_metadata_when_needed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plugin = FastAPIPlugin()

    fake_module = SimpleNamespace(__version__=None)
    monkeypatch.setitem(sys.modules, "fastapi", fake_module)

    monkeypatch.setattr(
        "modules.free.essentials.deployment.frameworks.fastapi.importlib_metadata.version",
        lambda _: "0.120.0",
    )

    assert plugin.validate_requirements() == []


def test_fastapi_validate_requirements_flags_old_version(monkeypatch: pytest.MonkeyPatch) -> None:
    plugin = FastAPIPlugin()

    fake_module = SimpleNamespace(__version__="0.118.2")
    monkeypatch.setitem(sys.modules, "fastapi", fake_module)

    errors = plugin.validate_requirements()

    assert errors
    assert "FastAPI version" in errors[0]
