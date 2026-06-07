"""Health checks tests for Api Keys."""

from __future__ import annotations


def test_api_keys_health_reports_operational_metadata(rendered_api_keys) -> None:  # type: ignore[no-untyped-def]
    runtime_mod = rendered_api_keys["runtime"]
    runtime = runtime_mod.ApiKeys({"pepper": "test-pepper", "rotation_days": 30})
    runtime.issue_key("owner-1", scopes=["read"])

    health = runtime.health_check()

    assert health["status"] == "ok"
    assert health["totals"]["active"] == 1
    assert health["metadata"]["module"] == "api_keys"
    assert "pepper_missing" not in health["issues"]
    assert health["telemetry"]["issued"] == 1
