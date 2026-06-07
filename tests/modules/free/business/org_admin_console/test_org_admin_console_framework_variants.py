from pathlib import Path


def test_org_admin_console_framework_templates_exist() -> None:
    root = Path("src/modules/free/business/org_admin_console/templates/variants")

    assert (root / "fastapi" / "org_admin_console.py.j2").exists()
    assert (root / "nestjs" / "org_admin_console.service.ts.j2").exists()
