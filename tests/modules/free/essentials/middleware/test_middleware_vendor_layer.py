"""Vendor layer presence for middleware module."""

from pathlib import Path

import yaml

from modules.free.essentials.middleware import generate


def test_vendor_files_exist() -> None:
    cfg_path = Path(generate.MODULE_ROOT) / "module.yaml"
    cfg = yaml.safe_load(cfg_path.read_text())
    vendor = cfg["generation"]["vendor"]
    files = vendor.get("files", [])
    assert files, "vendor files must be declared"

    for entry in files:
        template = entry.get("template")
        assert template, "vendor entry missing template"
        template_path = Path(generate.MODULE_ROOT) / template
        assert template_path.exists(), f"vendor template missing: {template}"
        relative = entry.get("relative")
        assert relative, "vendor entry missing relative output path"
