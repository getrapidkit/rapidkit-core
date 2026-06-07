import pytest


def test_analytics_dashboard_raises_domain_error_for_missing_resource(
    rendered_analytics_dashboard,
) -> None:
    vendor = rendered_analytics_dashboard["vendor"]
    dashboard = vendor.AnalyticsDashboard()

    with pytest.raises(vendor.AnalyticsDashboardError, match="metric name"):
        dashboard.record_metric("", 1)
