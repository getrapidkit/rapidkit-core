def test_analytics_dashboard_vendor_runtime_is_generated(rendered_analytics_dashboard) -> None:
    root = rendered_analytics_dashboard["root"]

    assert (
        root / ".rapidkit/vendor/analytics_dashboard/0.1.3/src/observability/analytics_dashboard.py"
    ).exists()
