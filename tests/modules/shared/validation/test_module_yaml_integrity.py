from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
MODULES_ROOT = REPO_ROOT / "src" / "modules"


def _iter_module_yaml_files() -> Iterator[Path]:
    for module_yaml in MODULES_ROOT.glob("**/module.yaml"):
        # Skip hidden directories (e.g. __pycache__)
        if any(part.startswith(".") for part in module_yaml.parts):
            continue
        yield module_yaml


_MODULE_YAML_FILES = tuple(sorted(_iter_module_yaml_files()))


@pytest.mark.parametrize(
    "module_yaml_path",
    _MODULE_YAML_FILES,
    ids=lambda path: str(path.relative_to(REPO_ROOT)),
)
def test_module_yaml_declares_existing_templates(module_yaml_path: Path) -> None:
    """Ensure every template referenced in module.yaml exists on disk."""

    config = yaml.safe_load(module_yaml_path.read_text(encoding="utf-8"))
    assert isinstance(config, dict), "module.yaml must resolve to a mapping"

    module_root = module_yaml_path.parent

    generation = config.get("generation")
    if not isinstance(generation, dict):
        pytest.skip("No generation configuration declared")

    vendor_cfg = generation.get("vendor")
    if isinstance(vendor_cfg, dict):
        for entry in vendor_cfg.get("files", []):
            template_ref = entry.get("template")
            assert isinstance(
                template_ref, str
            ), f"vendor template path must be a string: {module_yaml_path}"
            template_path = (module_root / template_ref).resolve()
            assert (
                template_path.exists()
            ), f"vendor template '{template_ref}' is missing for {module_yaml_path}"
            relative = entry.get("relative")
            assert isinstance(
                relative, str
            ), f"vendor relative path must be a string: {module_yaml_path}"
            assert relative.strip(), f"vendor relative path cannot be empty: {module_yaml_path}"

    variants_cfg = generation.get("variants")
    if not isinstance(variants_cfg, dict):
        return

    for variant_name, variant_cfg in variants_cfg.items():
        if not isinstance(variant_cfg, dict):
            continue
        for entry in variant_cfg.get("files", []):
            template_ref = entry.get("template")
            assert isinstance(
                template_ref, str
            ), f"variant '{variant_name}' template must be a string: {module_yaml_path}"
            template_path = (module_root / template_ref).resolve()
            assert (
                template_path.exists()
            ), f"template '{template_ref}' for variant {variant_name} is missing"
            output = entry.get("output")
            assert isinstance(
                output, str
            ), f"variant '{variant_name}' output must be a string: {module_yaml_path}"
            assert output.strip(), f"variant '{variant_name}' output cannot be empty"
