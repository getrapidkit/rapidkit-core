from pathlib import Path


def test_admin_console_framework_templates_exist() -> None:
    root = Path("src/modules/free/business/admin_console/templates/variants")

    assert (root / "fastapi" / "admin_console.py.j2").exists()
    assert (root / "nestjs" / "admin_console.service.ts.j2").exists()
