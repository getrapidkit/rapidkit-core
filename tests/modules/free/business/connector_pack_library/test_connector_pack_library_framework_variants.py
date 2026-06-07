from pathlib import Path


def test_connector_pack_library_framework_templates_exist() -> None:
    root = Path("src/modules/free/business/connector_pack_library/templates/variants")

    assert (root / "fastapi" / "connector_pack_library.py.j2").exists()
    assert (root / "nestjs" / "connector_pack_library.service.ts.j2").exists()
