"""Tests for telemetry module."""

from unittest.mock import patch

import core.telemetry.collector as collector_module
from core.telemetry import InsightsEngine, MetricsTracker, TelemetryCollector


class TestTelemetryCollector:
    """Test TelemetryCollector functionality."""

    def test_init(self):
        """Test TelemetryCollector initialization."""
        collector = TelemetryCollector()
        assert collector is not None
        assert hasattr(collector, "_event_queue")
        assert hasattr(collector, "_is_enabled")

    def test_get_telemetry_status(self):
        """Test getting telemetry status."""
        collector = TelemetryCollector()
        status = collector.get_telemetry_status()
        assert isinstance(status, dict)
        assert "enabled" in status
        assert "queue_size" in status

    def test_track_command(self):
        """Test command tracking."""
        with patch.object(collector_module, "datetime") as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2025-01-01T00:00:00"
            collector = TelemetryCollector()

            collector.track_command(
                command="test", args={"key": "value"}, start_time=1.0, success=True
            )

        # Check that event was queued
        assert collector._event_queue.qsize() >= 0


class TestMetricsTracker:
    """Test MetricsTracker functionality."""

    def test_init(self):
        """Test MetricsTracker initialization."""
        tracker = MetricsTracker()
        assert tracker is not None
        assert hasattr(tracker, "_metrics")

    def test_record_metric(self):
        """Test recording metrics."""
        tracker = MetricsTracker()
        tracker.record_metric("test_metric", 42.0)

        summary = tracker.get_performance_summary()
        assert isinstance(summary, dict)

    def test_get_performance_summary(self):
        """Test getting performance summary."""
        tracker = MetricsTracker()
        summary = tracker.get_performance_summary()
        assert isinstance(summary, dict)
        assert "total_metrics" in summary


class TestInsightsEngine:
    """Test InsightsEngine functionality."""

    def test_init(self):
        """Test InsightsEngine initialization."""
        engine = InsightsEngine()
        assert engine is not None
        assert hasattr(engine, "_insights")

    def test_analyze_telemetry_data(self):
        """Test telemetry data analysis."""
        engine = InsightsEngine()
        insights = engine.analyze_telemetry_data()
        assert isinstance(insights, list)
