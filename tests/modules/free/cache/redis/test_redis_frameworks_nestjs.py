"""Coverage-focused tests for the Redis NestJS framework plugin."""

from __future__ import annotations

import importlib
import json
from pathlib import Path


def _load_plugin():
    module = importlib.import_module("modules.free.cache.redis.frameworks.nestjs")
    return module.NestJSPlugin()


def test_nestjs_plugin_scaffold_generation(tmp_path: Path) -> None:
    plugin = _load_plugin()

    assert plugin.name == "nestjs"
    assert plugin.language == "typescript"
    assert plugin.display_name == "NestJS"
    assert "configuration" in plugin.get_template_mappings()
    assert "configuration" in plugin.get_output_paths()

    context = plugin.get_context_enrichments(
        {
            "rapidkit_vendor_nest_configuration_relative": "nestjs/runtime.js",
            "rapidkit_vendor_nest_service_relative": "nestjs/service.ts",
            "rapidkit_vendor_nest_module_relative": "nestjs/module.ts",
            "rapidkit_vendor_nest_index_relative": "nestjs/index.ts",
            "rapidkit_vendor_nest_validation_relative": "nestjs/validation.ts",
        }
    )
    assert context["framework"] == "nestjs"
    assert context["language"] == "typescript"

    assert plugin.validate_requirements() == []

    plugin.pre_generation_hook(tmp_path)
    config_dir = tmp_path / "src" / "modules" / "free" / "cache" / "redis"
    assert (config_dir / "redis.module.ts").parent.exists()
    assert (tmp_path / "tests" / "modules" / "integration" / "cache" / "redis").exists()

    tsconfig_path = tmp_path / "tsconfig.json"
    package_path = tmp_path / "package.json"
    assert tsconfig_path.exists()
    assert package_path.exists()

    # Ensure missing compiler options are added for existing tsconfig files.
    tsconfig_path.write_text(
        json.dumps({"compilerOptions": {"module": "commonjs"}}), encoding="utf-8"
    )
    type(plugin)._ensure_tsconfig(plugin, tsconfig_path)
    updated_tsconfig = json.loads(tsconfig_path.read_text(encoding="utf-8"))
    assert "target" in updated_tsconfig.get("compilerOptions", {})

    # Invalid JSON should be handled gracefully without raising.
    tsconfig_path.write_text("not-json", encoding="utf-8")
    type(plugin)._ensure_tsconfig(plugin, tsconfig_path)

    # Ensure missing dependencies are populated for package.json updates.
    package_path.write_text(json.dumps({"dependencies": {}}), encoding="utf-8")
    type(plugin)._ensure_package_json(plugin, package_path)
    updated_package = json.loads(package_path.read_text(encoding="utf-8"))
    assert "@nestjs/common" in updated_package.get("dependencies", {})

    # Invalid JSON should be ignored without raising.
    package_path.write_text("not-json", encoding="utf-8")
    type(plugin)._ensure_package_json(plugin, package_path)

    plugin.post_generation_hook(tmp_path)

    docs = plugin.get_documentation_urls()
    assert "framework_docs" in docs
    assert plugin.get_dependencies()
    assert plugin.get_dev_dependencies()
    assert plugin.get_example_configurations()
