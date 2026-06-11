def test_analytics_dashboard_vendor_runtime_is_generated(rendered_analytics_dashboard) -> None:
    root = rendered_analytics_dashboard["root"]
    config = rendered_analytics_dashboard["config"]

    assert (
        root
        / ".rapidkit"
        / "vendor"
        / config["name"]
        / config["version"]
        / "src/modules/free/observability/analytics_dashboard/analytics_dashboard.py"
    ).exists()
