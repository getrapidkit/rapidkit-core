"""Additional core tests to increase coverage for telemetry and metrics."""

import json
from pathlib import Path

from core.telemetry.collector import TelemetryCollector
from core.telemetry.insights import InsightsEngine
from core.telemetry.metrics import MetricsTracker


def make_sample_event(command: str, duration: float, success: bool = True):
    return {
        "event_id": "evt-1",
        "timestamp": "2025-01-01T00:00:00Z",
        "event_type": "command",
        "command": command,
        "args": {"k": "v"},
        "duration_ms": duration,
        "success": success,
    }


def test_insights_engine_with_files(tmp_path: Path):
    # create telemetry files readable by InsightsEngine
    td = tmp_path / "telemetry"
    td.mkdir()
    events = [
        make_sample_event("cmd_a", 50.0),
        make_sample_event("cmd_b", 2000.0),
        make_sample_event("cmd_a", 12000.0, success=False),
    ]
    batch = {"events": events}
    fpath = td / "telemetry_batch_20250101_000000_abcd1234.json"
    fpath.write_text(json.dumps(batch), encoding="utf-8")

    engine = InsightsEngine(telemetry_dir=td)
    insights = engine.analyze_telemetry_data()
    assert isinstance(insights, list)
    # exercise export
    out = tmp_path / "insights_out.json"
    engine.export_insights(out)
    assert out.exists()


def test_telemetry_collector_basic(tmp_path: Path):
    collector = TelemetryCollector()
    # point to a temp telemetry dir so persistence doesn't error
    collector._telemetry_dir = tmp_path
    collector.track_command("tst", {}, start_time=0.0, success=True)
    # should queue at least 1
    assert collector.get_telemetry_status()
    # flush should not raise
    collector.flush_events()


def test_metrics_tracker_varied():
    tracker = MetricsTracker()
    for i in range(10):
        tracker.record_metric("m1", float(i))
    tracker.record_metric("m2", 100.0)
    summary = tracker.get_performance_summary()
    assert "total_metrics" in summary
    MIN_EXPECTED_METRICS = 2
    assert summary["total_metrics"] >= MIN_EXPECTED_METRICS
