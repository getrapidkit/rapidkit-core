from pathlib import Path

import yaml


def test_analytics_dashboard_manifest_is_stable_free_module() -> None:
    data = yaml.safe_load(
        Path("src/modules/free/observability/analytics_dashboard/module.yaml").read_text(
            encoding="utf-8"
        )
    )

    assert data["tier"] == "free"
    assert data["category"] == "observability"
    assert data["status"] == "stable"
    assert data["metadata"]["enterprise_ready"] is True
    assert "fastapi.standard" in data["profile_inherits"]
    assert "nestjs.standard" in data["profile_inherits"]
