"""Vendor layer presence for deployment module."""

from pathlib import Path

import yaml

from modules.free.essentials.deployment import generate


def test_vendor_templates_exist() -> None:
    cfg = yaml.safe_load((Path(generate.MODULE_ROOT) / "module.yaml").read_text())
    files = cfg["generation"]["vendor"].get("files", [])
    assert files, "vendor files must be declared"

    for entry in files:
        template = entry.get("template")
        assert template, "vendor entry missing template"
        template_path = Path(generate.MODULE_ROOT) / template
        assert template_path.exists(), f"vendor template missing: {template}"
        assert entry.get("relative"), "vendor entry missing relative output"
