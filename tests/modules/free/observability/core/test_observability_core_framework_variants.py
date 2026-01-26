"""Validate observability_core module declares both framework variants."""

from pathlib import Path

import yaml

from modules.free.observability.core import generate


def test_variants_present() -> None:
    cfg = yaml.safe_load((Path(generate.MODULE_ROOT) / "module.yaml").read_text())
    variants = cfg.get("generation", {}).get("variants", {})
    # The runner installs with kit profile names (e.g. "nestjs.standard"), so
    # module manifests must expose profile-name variants as aliases.
    expected = {"fastapi", "nestjs", "fastapi.standard", "fastapi.ddd", "nestjs.standard"}
    assert expected.issubset(set(variants))
    for name, spec in variants.items():
        files = spec.get("files", [])
        assert files, f"variant {name} should declare files"
