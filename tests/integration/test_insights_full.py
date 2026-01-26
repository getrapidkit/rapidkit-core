"""Targeted tests for InsightsEngine to increase coverage."""

import json
from datetime import datetime, timedelta
from pathlib import Path

from core.telemetry.insights import InsightsEngine


def make_event(
    command: str,
    duration_ms: float = 0.0,
    success: bool = True,
    ts: str | None = None,
    args: dict | None = None,
):
    return {
        "event_id": f"evt-{command}-{duration_ms}",
        "timestamp": ts or (datetime.now().isoformat() + "Z"),
        "event_type": "command_execution",
        "command": command,
        "args": args or {},
        "duration_ms": duration_ms,
        "success": success,
    }


def write_batch(path: Path, events: list):
    path.write_text(json.dumps({"events": events}), encoding="utf-8")


def test_insights_engine_triggers_various(tmp_path: Path):
    td = tmp_path / "telemetry"
    td.mkdir()

    now = datetime.now()

    # Create an old file (should be ignored by recent filter)
    old_name = td / "telemetry_batch_20000101_000000_old.json"
    write_batch(old_name, [make_event("old_cmd", 10)])

    # Usage pattern: create 12 events for 'popular' to exceed SIGNIFICANT_USAGE_THRESHOLD (10)
    popular_events = [make_event("popular", 10.0) for _ in range(12)]
    write_batch(
        td / f"telemetry_batch_{now.strftime('%Y%m%d')}_{now.strftime('%H%M%S')}_popular.json",
        popular_events,
    )

    # Performance: create >5 samples with high durations for 'slow_cmd'
    slow_events = [make_event("slow_cmd", d) for d in [6000, 7000, 8000, 9000, 11000]]

    # Error pattern: create 6 executions for 'err_cmd' with 4 failures => error rate 66%
    FAIL_THRESHOLD = 2
    err_events = [make_event("err_cmd", 100.0, success=(i < FAIL_THRESHOLD)) for i in range(6)]

    # Security: include sensitive arg keys
    sec_events = [make_event("sec_cmd", 10.0, args={"password": "secret"})]

    mixed = slow_events + err_events + sec_events
    write_batch(
        td
        / f"telemetry_batch_{(now + timedelta(seconds=1)).strftime('%Y%m%d')}_{(now + timedelta(seconds=1)).strftime('%H%M%S')}_mixed.json",
        mixed,
    )

    engine = InsightsEngine(telemetry_dir=td)
    insights = engine.analyze_telemetry_data()

    # We expect at least one performance insight, one usage insight, one error insight, and one security insight
    categories = {ins.category for ins in insights}
    assert "performance" in categories
    assert "usage" in categories
    assert "reliability" in categories
    assert "security" in categories

    # test helper getters
    perf = engine.get_insights_by_category("performance")
    assert isinstance(perf, list)

    # test export
    out = tmp_path / "out_insights.json"
    engine.export_insights(out)
    assert out.exists()

    # top insights should return a list limited by default
    TOP_LIMIT = 10
    tops = engine.get_top_insights()
    assert isinstance(tops, list)
    assert len(tops) <= TOP_LIMIT
