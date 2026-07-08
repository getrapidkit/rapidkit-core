from pathlib import Path

import pytest

from modules.free.business.admin_console import generate
from modules.free.business.admin_console.frameworks import (
    FrameworkPlugin,
    get_plugin,
    list_available_plugins,
    refresh_plugin_registry,
)
from modules.free.business.admin_console.frameworks.fastapi import FastAPIPlugin
from modules.free.business.admin_console.frameworks.nestjs import NestJSPlugin


def test_admin_console_framework_registry_contract() -> None:
    refresh_plugin_registry(auto_discover=False)

    available = list_available_plugins()

    assert available == {"fastapi": "FastAPI", "nestjs": "NestJS"}
    assert isinstance(get_plugin("fastapi"), FastAPIPlugin)
    assert isinstance(get_plugin("nestjs"), NestJSPlugin)
    assert issubclass(FastAPIPlugin, FrameworkPlugin)
    assert issubclass(NestJSPlugin, FrameworkPlugin)


def test_admin_console_fastapi_plugin_contract(tmp_path: Path) -> None:
    plugin = FastAPIPlugin()
    base_context = {"module_name": "admin_console"}

    assert plugin.name == "fastapi"
    assert plugin.language == "python"
    assert plugin.display_name == "FastAPI"
    assert plugin.validate_requirements() == []
    assert "fastapi>=0.139.0" in plugin.get_dependencies()
    assert "httpx>=0.27.0" in plugin.get_dev_dependencies()
    assert plugin.get_template_mappings()["runtime"].endswith("admin_console.py.j2")
    assert (
        plugin.get_output_paths()["router"]
        == "src/modules/free/business/admin_console/routers/business/admin_console.py"
    )
    assert plugin.get_context_enrichments(base_context)["framework_display_name"] == "FastAPI"

    plugin.pre_generation_hook(tmp_path)
    assert (
        tmp_path
        / "src"
        / "modules"
        / "free"
        / "business"
        / "admin_console"
        / "routers"
        / "business"
    ).is_dir()
    assert (tmp_path / "src" / "health").is_dir()
    plugin.post_generation_hook(tmp_path)


def test_admin_console_nestjs_plugin_contract(tmp_path: Path) -> None:
    plugin = NestJSPlugin()
    base_context = {"module_name": "admin_console"}

    assert plugin.name == "nestjs"
    assert plugin.language == "typescript"
    assert plugin.display_name == "NestJS"
    assert plugin.validate_requirements() == []
    assert "@nestjs/common>=10.0.0" in plugin.get_dependencies()
    assert "ts-jest>=29.0.0" in plugin.get_dev_dependencies()
    assert plugin.get_template_mappings()["controller"].endswith("admin_console.controller.ts.j2")
    assert (
        plugin.get_output_paths()["module"]
        == "src/modules/free/business/admin_console/admin_console.module.ts"
    )
    assert plugin.get_context_enrichments(base_context)["module_name"] == "admin_console"

    plugin.pre_generation_hook(tmp_path)
    assert (tmp_path / "src").is_dir()
    plugin.post_generation_hook(tmp_path)


def test_admin_console_generate_wrappers_emit_expected_files(tmp_path: Path) -> None:
    config = generate.load_module_config()
    context = generate.build_base_context(config)
    renderer = generate.AdminConsoleModuleGenerator().create_renderer()

    generate.generate_vendor_files(config, tmp_path, renderer, context)
    generate.generate_variant_files("fastapi", tmp_path, renderer, context)
    generate.generate_variant_files("nestjs", tmp_path, renderer, context)

    assert (tmp_path / ".rapidkit" / "vendor" / "admin_console" / config["version"]).is_dir()
    assert (
        tmp_path / "src" / "modules" / "free" / "business" / "admin_console" / "admin_console.py"
    ).exists()
    assert (
        tmp_path
        / "src"
        / "modules"
        / "free"
        / "business"
        / "admin_console"
        / "routers"
        / "business"
        / "admin_console.py"
    ).exists()
    assert (
        tmp_path
        / "src"
        / "modules"
        / "free"
        / "business"
        / "admin_console"
        / "admin_console.service.ts"
    ).exists()


def test_admin_console_generator_error_carries_exit_context() -> None:
    error = generate.GeneratorError("bad input", exit_code=7, context={"field": "framework"})

    assert error.exit_code == 7
    assert error.context["field"] == "framework"
    assert error.context["exit_code"] == 7


def test_admin_console_vendor_primary_path_falls_back() -> None:
    assert generate.infer_vendor_primary_path({}) == generate.VENDOR_RELATIVE


def test_admin_console_main_rejects_missing_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(generate.sys, "argv", ["generate.py"])

    with pytest.raises(generate.GeneratorError) as exc:
        generate.main()

    assert exc.value.exit_code == 2
    assert "Available frameworks" in exc.value.message
