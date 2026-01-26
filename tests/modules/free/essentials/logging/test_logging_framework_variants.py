"""Validate logging module declares both framework variants."""

from pathlib import Path

import yaml

from modules.free.essentials.logging import generate


def test_variants_present() -> None:
    cfg_path = Path(generate.MODULE_ROOT) / "module.yaml"
    cfg = yaml.safe_load(cfg_path.read_text())
    variants = cfg.get("generation", {}).get("variants", {})
    base_variants = {"fastapi", "nestjs"}
    assert base_variants.issubset(set(variants)), "missing required base variants"
    allowed_prefixes = tuple(base_variants)
    for name, spec in variants.items():
        assert name.startswith(allowed_prefixes), f"unexpected variant namespace: {name}"
        files = spec.get("files", [])
        assert files, f"variant {name} should declare files"
