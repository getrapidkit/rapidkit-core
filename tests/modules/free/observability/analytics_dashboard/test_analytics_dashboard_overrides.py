from modules.free.observability.analytics_dashboard import overrides


def test_analytics_dashboard_overrides_contract_loads() -> None:
    assert hasattr(overrides, "AnalyticsDashboardOverrides")
