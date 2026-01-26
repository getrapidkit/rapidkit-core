"""Validate middleware module declares both framework variants."""

from pathlib import Path

import yaml

from modules.free.essentials.middleware import generate


def test_variants_present() -> None:
    cfg_path = Path(generate.MODULE_ROOT) / "module.yaml"
    cfg = yaml.safe_load(cfg_path.read_text())
    variants = cfg.get("generation", {}).get("variants", {})
    assert {"fastapi", "nestjs"}.issubset(set(variants))
    for name, spec in variants.items():
        files = spec.get("files", [])
        assert files, f"variant {name} should declare files"
