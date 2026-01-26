"""Tests covering the vendor layer templates."""

from __future__ import annotations

from modules.free.business.storage import generate


def test_vendor_types_template_exports_symbols():
    renderer = generate.TemplateRenderer()
    config = generate.load_module_config()
    context = generate.build_base_context(config)
    template = generate.MODULE_ROOT / "templates/base/storage_types.py.j2"

    rendered = renderer.render(template, context)
    assert "FileMetadata" in rendered
    assert "StorageAdapter" in rendered
