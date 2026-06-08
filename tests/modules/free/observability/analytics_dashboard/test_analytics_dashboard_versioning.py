import yaml

from modules.free.observability.analytics_dashboard.generate import (
    MODULE_ROOT,
    AnalyticsDashboardModuleGenerator,
)


def test_analytics_dashboard_generator_version_matches_manifest() -> None:
    generator = AnalyticsDashboardModuleGenerator()
    config = generator.load_module_config()
    manifest = yaml.safe_load((MODULE_ROOT / "module.yaml").read_text(encoding="utf-8"))

    assert config["version"] == manifest["version"]
