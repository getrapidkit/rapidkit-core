import importlib.util
import sys
from pathlib import Path

from modules.free.observability.analytics_dashboard.generate import (
    AnalyticsDashboardModuleGenerator,
)


def _load_vendor(path: Path) -> object:
    spec = importlib.util.spec_from_file_location("integration_analytics_dashboard_vendor", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generated vendor from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_analytics_dashboard_integration_runtime_smoke(tmp_path: Path) -> None:
    generator = AnalyticsDashboardModuleGenerator()
    config = generator.load_module_config()
    context = generator.build_base_context(config)
    renderer = generator.create_renderer()
    generator.generate_vendor_files(config, tmp_path, renderer, context)
    vendor = _load_vendor(
        tmp_path
        / ".rapidkit"
        / "vendor"
        / "analytics_dashboard"
        / "0.1.3"
        / "src/observability/analytics_dashboard.py"
    )
    console = vendor.AnalyticsDashboard()
    console.record_metric("orders", 2)
    console.add_widget(title="Orders", metric="orders")

    assert console.snapshot().widget_count == 1
