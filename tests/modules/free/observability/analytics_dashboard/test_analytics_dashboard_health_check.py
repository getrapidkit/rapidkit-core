def test_analytics_dashboard_health_reports_runtime_state(rendered_analytics_dashboard) -> None:
    vendor = rendered_analytics_dashboard["vendor"]
    dashboard = vendor.AnalyticsDashboard()
    dashboard.record_metric("orders", 2)
    dashboard.add_widget(title="Orders", metric="orders")
    dashboard.snapshot()

    health = dashboard.health()
    assert health["metrics"] == 1
    assert health["widgets"] == 1
    assert health["snapshots"] == 1
