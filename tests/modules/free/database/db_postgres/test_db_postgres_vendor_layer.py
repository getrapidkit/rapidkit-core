"""Vendor layer coverage for Db Postgres."""

from __future__ import annotations

import yaml


def test_vendor_configuration_declares_files(module_config: dict[str, object]) -> None:
    vendor = module_config.get("generation", {}).get("vendor", {})  # type: ignore[assignment]
    assert isinstance(vendor, dict)
    assert vendor.get("root") == ".rapidkit/vendor"
    files = vendor.get("files", [])
    assert any(
        isinstance(entry, dict)
        and entry.get("relative") == "src/modules/free/database/db_postgres/postgres.py"
        for entry in files
    )


def test_snippet_configuration(module_root) -> None:
    snippets_path = module_root / "config/snippets.yaml"
    data = yaml.safe_load(snippets_path.read_text(encoding="utf-8"))
    snippets = data.get("snippets", [])
    assert snippets, "snippets configuration must define at least one bundle"
    first = snippets[0]
    assert first.get("id") == "db_postgres_settings_fields"
    assert "settings-fields" in str(first.get("anchor"))
    assert "settings.py" in str(first.get("target"))
