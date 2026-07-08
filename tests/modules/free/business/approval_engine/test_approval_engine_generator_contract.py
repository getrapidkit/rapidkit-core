from pathlib import Path

import pytest

from modules.free.business.approval_engine import generate
from modules.free.business.approval_engine.frameworks import (
    FrameworkPlugin,
    get_plugin,
    list_available_plugins,
    refresh_plugin_registry,
)
from modules.free.business.approval_engine.frameworks.fastapi import FastAPIPlugin
from modules.free.business.approval_engine.frameworks.nestjs import NestJSPlugin


def test_approval_engine_framework_registry_contract() -> None:
    refresh_plugin_registry(auto_discover=False)

    available = list_available_plugins()

    assert available == {"fastapi": "FastAPI", "nestjs": "NestJS"}
    assert isinstance(get_plugin("fastapi"), FastAPIPlugin)
    assert isinstance(get_plugin("nestjs"), NestJSPlugin)
    assert issubclass(FastAPIPlugin, FrameworkPlugin)
    assert issubclass(NestJSPlugin, FrameworkPlugin)


def test_approval_engine_fastapi_plugin_contract(tmp_path: Path) -> None:
    plugin = FastAPIPlugin()
    base_context = {"module_name": "approval_engine"}

    assert plugin.name == "fastapi"
    assert plugin.language == "python"
    assert plugin.display_name == "FastAPI"
    assert plugin.validate_requirements() == []
    assert "fastapi>=0.139.0" in plugin.get_dependencies()
    assert "httpx>=0.27.0" in plugin.get_dev_dependencies()
    assert plugin.get_template_mappings()["runtime"].endswith("approval_engine.py.j2")
    assert (
        plugin.get_output_paths()["router"]
        == "src/modules/free/business/approval_engine/routers/business/approval_engine.py"
    )
    assert plugin.get_context_enrichments(base_context)["framework_display_name"] == "FastAPI"

    plugin.pre_generation_hook(tmp_path)
    assert (
        tmp_path
        / "src"
        / "modules"
        / "free"
        / "business"
        / "approval_engine"
        / "routers"
        / "business"
    ).is_dir()
    assert (tmp_path / "src" / "health").is_dir()
    plugin.post_generation_hook(tmp_path)


def test_approval_engine_nestjs_plugin_contract(tmp_path: Path) -> None:
    plugin = NestJSPlugin()
    base_context = {"module_name": "approval_engine"}

    assert plugin.name == "nestjs"
    assert plugin.language == "typescript"
    assert plugin.display_name == "NestJS"
    assert plugin.validate_requirements() == []
    assert "@nestjs/common>=10.0.0" in plugin.get_dependencies()
    assert "ts-jest>=29.0.0" in plugin.get_dev_dependencies()
    assert plugin.get_template_mappings()["controller"].endswith("approval_engine.controller.ts.j2")
    assert (
        plugin.get_output_paths()["module"]
        == "src/modules/free/business/approval_engine/approval_engine.module.ts"
    )
    assert plugin.get_context_enrichments(base_context)["module_name"] == "approval_engine"

    plugin.pre_generation_hook(tmp_path)
    assert (tmp_path / "src").is_dir()
    plugin.post_generation_hook(tmp_path)


def test_approval_engine_generate_wrappers_emit_expected_files(tmp_path: Path) -> None:
    config = generate.load_module_config()
    context = generate.build_base_context(config)
    renderer = generate.ApprovalEngineModuleGenerator().create_renderer()

    generate.generate_vendor_files(config, tmp_path, renderer, context)
    generate.generate_variant_files("fastapi", tmp_path, renderer, context)
    generate.generate_variant_files("nestjs", tmp_path, renderer, context)

    assert (tmp_path / ".rapidkit" / "vendor" / "approval_engine" / config["version"]).is_dir()
    assert (
        tmp_path
        / "src"
        / "modules"
        / "free"
        / "business"
        / "approval_engine"
        / "approval_engine.py"
    ).exists()
    assert (
        tmp_path
        / "src"
        / "modules"
        / "free"
        / "business"
        / "approval_engine"
        / "routers"
        / "business"
        / "approval_engine.py"
    ).exists()
    assert (
        tmp_path
        / "src"
        / "modules"
        / "free"
        / "business"
        / "approval_engine"
        / "approval_engine.service.ts"
    ).exists()


def test_approval_engine_generator_error_carries_exit_context() -> None:
    error = generate.GeneratorError("bad input", exit_code=7, context={"field": "framework"})

    assert error.exit_code == 7
    assert error.context["field"] == "framework"
    assert error.context["exit_code"] == 7


def test_approval_engine_vendor_primary_path_falls_back() -> None:
    assert generate.infer_vendor_primary_path({}) == generate.VENDOR_RELATIVE


def test_approval_engine_vendor_primary_path_reads_config() -> None:
    config = {
        "generation": {
            "vendor": {
                "files": [
                    {
                        "template": "templates/base/approval_engine.py.j2",
                        "relative": "custom/path/approval_engine.py",
                    }
                ]
            }
        }
    }

    assert generate.infer_vendor_primary_path(config) == "custom/path/approval_engine.py"


def test_approval_engine_main_rejects_missing_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(generate.sys, "argv", ["generate.py"])

    with pytest.raises(generate.GeneratorError) as exc:
        generate.main()

    assert exc.value.exit_code == 2
    assert "Available frameworks" in exc.value.message
