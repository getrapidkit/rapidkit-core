import importlib.util
import sys
from pathlib import Path

import pytest


@pytest.fixture(name="module_test_context")
def module_test_context_fixture(tmp_path: Path) -> dict[str, object]:
    """Provide an isolated workspace for Analytics Dashboard module tests."""

    working_dir = tmp_path / "analytics_dashboard"
    working_dir.mkdir(parents=True, exist_ok=True)
    return {
        "module_name": "analytics_dashboard",
        "workspace": working_dir,
        "context_file": working_dir / "context.json",
    }


def _load_module(name: str, path: Path) -> object:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generated module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def rendered_analytics_dashboard(tmp_path: Path) -> dict[str, object]:
    from modules.free.observability.analytics_dashboard.generate import (
        AnalyticsDashboardModuleGenerator,
    )

    generator = AnalyticsDashboardModuleGenerator()
    config = generator.load_module_config()
    context = generator.build_base_context(config)
    renderer = generator.create_renderer()
    generator.generate_vendor_files(config, tmp_path, renderer, context)
    vendor_path = (
        tmp_path
        / ".rapidkit"
        / "vendor"
        / config["name"]
        / config["version"]
        / "src"
        / "observability"
        / "analytics_dashboard.py"
    )
    return {
        "root": tmp_path,
        "vendor": _load_module("generated_analytics_dashboard_vendor", vendor_path),
    }
