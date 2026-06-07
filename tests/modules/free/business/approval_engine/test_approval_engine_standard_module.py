from pathlib import Path

import yaml


def test_approval_engine_manifest_is_stable_free_module() -> None:
    data = yaml.safe_load(
        Path("src/modules/free/business/approval_engine/module.yaml").read_text(encoding="utf-8")
    )

    assert data["tier"] == "free"
    assert data["category"] == "business"
    assert "fastapi.standard" in data["profile_inherits"]
    assert "nestjs.standard" in data["profile_inherits"]
