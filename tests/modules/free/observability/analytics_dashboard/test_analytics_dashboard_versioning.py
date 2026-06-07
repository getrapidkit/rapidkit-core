from modules.free.observability.analytics_dashboard.generate import (
    AnalyticsDashboardModuleGenerator,
)


def test_analytics_dashboard_generator_version_matches_manifest() -> None:
    generator = AnalyticsDashboardModuleGenerator()
    config = generator.load_module_config()

    assert config["version"] == "0.1.3"
