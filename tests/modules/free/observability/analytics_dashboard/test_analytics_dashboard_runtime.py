from __future__ import annotations

import pytest


def test_analytics_dashboard_records_metrics_widgets_and_snapshots(
    rendered_analytics_dashboard,
) -> None:
    vendor = rendered_analytics_dashboard["vendor"]
    dashboard = vendor.AnalyticsDashboard()
    dashboard.record_metric("orders", 2, dimensions={"tier": "pro"})
    dashboard.record_metric("orders", 4, dimensions={"tier": "pro"})
    dashboard.record_metric("orders", 1, dimensions={"tier": "free"})
    dashboard.add_widget(title="Pro Orders", metric="orders", filters={"tier": "pro"})

    summary = dashboard.summarize_metric("orders", filters={"tier": "pro"})
    snapshot = dashboard.snapshot()

    assert summary["count"] == 2
    assert summary["total"] == "6"
    assert snapshot.widget_count == 1
    assert snapshot.metrics["Pro Orders"]["count"] == 2
    assert dashboard.health()["points"] == 3


def test_analytics_dashboard_validates_metric_and_widget_input(
    rendered_analytics_dashboard,
) -> None:
    vendor = rendered_analytics_dashboard["vendor"]
    dashboard = vendor.AnalyticsDashboard()

    with pytest.raises(vendor.AnalyticsDashboardError, match="metric name"):
        dashboard.record_metric("", 1)
    with pytest.raises(vendor.AnalyticsDashboardError, match="widget"):
        dashboard.add_widget(title="", metric="orders")
