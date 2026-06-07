from pathlib import Path


def test_support_center_framework_templates_exist() -> None:
    root = Path("src/modules/free/business/support_center/templates/variants")

    assert (root / "fastapi" / "support_center.py.j2").exists()
    assert (root / "nestjs" / "support_center.service.ts.j2").exists()
