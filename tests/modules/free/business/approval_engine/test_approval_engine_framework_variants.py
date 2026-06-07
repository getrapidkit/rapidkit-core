from pathlib import Path


def test_approval_engine_framework_templates_exist() -> None:
    root = Path("src/modules/free/business/approval_engine/templates/variants")

    assert (root / "fastapi" / "approval_engine.py.j2").exists()
    assert (root / "nestjs" / "approval_engine.service.ts.j2").exists()
