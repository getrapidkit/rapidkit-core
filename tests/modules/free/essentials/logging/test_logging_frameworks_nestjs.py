"""Coverage-focused tests for the Logging NestJS framework plugin."""

from __future__ import annotations

import importlib
import json
from pathlib import Path


def _load_plugin():
    module = importlib.import_module("modules.free.essentials.logging.frameworks.nestjs")
    return module.NestJSPlugin()


def test_logging_nestjs_plugin_scaffold(tmp_path: Path) -> None:
    plugin = _load_plugin()

    assert plugin.name == "nestjs"
    assert plugin.language == "typescript"
    assert plugin.display_name == "NestJS"
    assert "configuration" in plugin.get_template_mappings()
    assert "configuration" in plugin.get_output_paths()

    context = plugin.get_context_enrichments({"module_name": "free/essentials/logging"})
    assert context["framework"] == "nestjs"
    assert context["module_slug"] == "logging"
    assert context["module_kebab"] == "logging"

    assert plugin.validate_requirements() == []

    plugin.pre_generation_hook(tmp_path)
    assert (tmp_path / "src" / "modules" / "free" / "essentials" / "logging").exists()
    assert (tmp_path / "tests" / "modules" / "integration" / "essentials" / "logging").exists()

    tsconfig_path = tmp_path / "tsconfig.json"
    package_path = tmp_path / "package.json"
    assert tsconfig_path.exists()
    assert package_path.exists()

    tsconfig_path.write_text(
        json.dumps({"compilerOptions": {"module": "commonjs"}}), encoding="utf-8"
    )
    type(plugin)._ensure_tsconfig(plugin, tsconfig_path)
    updated_tsconfig = json.loads(tsconfig_path.read_text(encoding="utf-8"))
    assert "target" in updated_tsconfig.get("compilerOptions", {})

    tsconfig_path.write_text("not-json", encoding="utf-8")
    type(plugin)._ensure_tsconfig(plugin, tsconfig_path)

    package_path.write_text(json.dumps({"dependencies": {}}), encoding="utf-8")
    type(plugin)._ensure_package_json(plugin, package_path)
    updated_package = json.loads(package_path.read_text(encoding="utf-8"))
    assert "@nestjs/common" in updated_package.get("dependencies", {})

    package_path.write_text("not-json", encoding="utf-8")
    type(plugin)._ensure_package_json(plugin, package_path)

    plugin.post_generation_hook(tmp_path)

    assert plugin.get_documentation_urls()
    assert plugin.get_example_configurations()
    assert plugin.get_dependencies()
    assert plugin.get_dev_dependencies()
