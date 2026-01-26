"""Validate deployment module declares both framework variants."""

from pathlib import Path

import yaml

from modules.free.essentials.deployment import generate


def test_variants_present() -> None:
    cfg = yaml.safe_load((Path(generate.MODULE_ROOT) / "module.yaml").read_text())
    variants = cfg.get("generation", {}).get("variants", {})
    # The module must always expose the canonical framework variants.
    # Additional aliases (e.g. `fastapi.standard`) may be present for
    # compatibility with kit profile names.
    assert {"fastapi", "nestjs"}.issubset(set(variants))
    for name, spec in variants.items():
        files = spec.get("files", [])
        assert files, f"variant {name} should declare files"
