import pytest


def test_analytics_dashboard_validates_required_input(rendered_analytics_dashboard) -> None:
    vendor = rendered_analytics_dashboard["vendor"]
    dashboard = vendor.AnalyticsDashboard()

    with pytest.raises(vendor.AnalyticsDashboardError, match="widget"):
        dashboard.add_widget(title="", metric="orders")
