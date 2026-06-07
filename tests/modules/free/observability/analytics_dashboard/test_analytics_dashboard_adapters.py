def test_analytics_dashboard_exposes_runtime_contract(rendered_analytics_dashboard) -> None:
    vendor = rendered_analytics_dashboard["vendor"]

    assert hasattr(vendor, "AnalyticsDashboard")
    assert hasattr(vendor, "MetricPoint")
    assert hasattr(vendor, "DashboardWidget")
    assert hasattr(vendor, "DashboardSnapshot")
