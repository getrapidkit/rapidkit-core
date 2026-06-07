from pathlib import Path

import yaml


def test_org_admin_console_manifest_is_stable_free_module() -> None:
    data = yaml.safe_load(
        Path("src/modules/free/business/org_admin_console/module.yaml").read_text(encoding="utf-8")
    )

    assert data["tier"] == "free"
    assert data["category"] == "business"
    assert data["status"] == "stable"
    assert data["metadata"]["enterprise_ready"] is True
    assert "fastapi.standard" in data["profile_inherits"]
    assert "nestjs.standard" in data["profile_inherits"]
