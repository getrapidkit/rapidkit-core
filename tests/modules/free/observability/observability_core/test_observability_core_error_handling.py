"""Generator error handling tests for Observability Core."""

from __future__ import annotations

import copy

import pytest

from modules.free.observability.core import generate


def _build_context(generator: generate.ObservabilityModuleGenerator) -> dict[str, object]:
    config = generator.load_module_config()
    base_context = generator.build_base_context(config)
    return generator.apply_base_context_overrides(base_context)


def test_generate_variant_unknown_framework_raises(tmp_path) -> None:  # type: ignore[no-untyped-def]
    generator = generate.ObservabilityModuleGenerator()
    context = _build_context(generator)
    renderer = generator.create_renderer()

    with pytest.raises(generate.GeneratorError) as exc:
        generator.generate_variant_files("unknown-framework", tmp_path, renderer, context)

    assert "framework plugin" in str(exc.value).lower()


def test_generate_vendor_missing_template(tmp_path) -> None:  # type: ignore[no-untyped-def]
    generator = generate.ObservabilityModuleGenerator()
    config = copy.deepcopy(generator.load_module_config())
    vendor_files = config["generation"]["vendor"]["files"]  # type: ignore[index]
    vendor_files[0]["template"] = "templates/base/does_not_exist.py.j2"

    context = generator.apply_base_context_overrides(generator.build_base_context(config))
    renderer = generator.create_renderer()

    with pytest.raises(generate.GeneratorError) as exc:
        generator.generate_vendor_files(config, tmp_path, renderer, context)

    assert "missing" in str(exc.value).lower()
