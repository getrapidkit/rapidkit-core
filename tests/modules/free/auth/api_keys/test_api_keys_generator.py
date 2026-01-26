"""Generator-level guardrails for Api Keys."""

from __future__ import annotations

from pathlib import Path


def test_generate_vendor_and_variant_outputs(
    api_keys_generator,
    module_config,
    tmp_path: Path,
) -> None:
    renderer = api_keys_generator.create_renderer()
    base_context = api_keys_generator.apply_base_context_overrides(
        api_keys_generator.build_base_context(module_config)
    )

    api_keys_generator.generate_vendor_files(module_config, tmp_path, renderer, base_context)
    vendor_root = (
        tmp_path
        / ".rapidkit"
        / "vendor"
        / str(base_context["rapidkit_vendor_module"])
        / str(base_context["rapidkit_vendor_version"])
        / "src"
    )
    vendor_expected = {
        vendor_root / "modules" / "free" / "auth" / "api_keys" / "api_keys.py",
        vendor_root / "health" / "api_keys.py",
        vendor_root / "modules" / "free" / "auth" / "api_keys" / "types" / "api_keys.py",
    }
    for artefact in vendor_expected:
        assert artefact.exists(), f"Expected vendor artefact {artefact}"
        assert artefact.read_text().strip(), f"Generated vendor file {artefact} is empty"

    config_file = (
        tmp_path
        / ".rapidkit"
        / "vendor"
        / str(base_context["rapidkit_vendor_module"])
        / str(base_context["rapidkit_vendor_version"])
        / "nestjs"
        / "configuration.js"
    )
    assert config_file.exists(), "Vendor configuration.js should be generated"
    assert config_file.read_text().strip(), "Generated configuration.js is empty"

    api_keys_generator.generate_variant_files("fastapi", tmp_path, renderer, base_context)
    fastapi_expected = {
        tmp_path / "src" / "modules" / "free" / "auth" / "api_keys" / "api_keys.py",
        tmp_path / "src" / "health" / "api_keys.py",
        tmp_path / "src" / "modules" / "free" / "auth" / "api_keys" / "routers" / "api_keys.py",
    }
    for artefact in fastapi_expected:
        assert artefact.exists(), f"Expected FastAPI artefact {artefact}"
        assert artefact.read_text().strip(), f"Generated FastAPI file {artefact} is empty"

    api_keys_generator.generate_variant_files("nestjs", tmp_path, renderer, base_context)
    service_file = (
        tmp_path / "src" / "modules" / "free" / "auth" / "api_keys" / "api-keys.service.ts"
    )
    controller_file = (
        tmp_path / "src" / "modules" / "free" / "auth" / "api_keys" / "api-keys.controller.ts"
    )
    module_file = tmp_path / "src" / "modules" / "free" / "auth" / "api_keys" / "api-keys.module.ts"

    for artefact in (service_file, controller_file, module_file):
        assert artefact.exists(), f"Expected NestJS artefact {artefact}"
        assert artefact.read_text().strip(), f"Generated NestJS file {artefact} is empty"

    controller_src = controller_file.read_text()
    assert (
        "@Controller('api-keys')" in controller_src or '@Controller("api-keys")' in controller_src
    ), "API Keys controller should mount api-keys route"
    assert "@Get('health')" in controller_src or '@Get("health")' in controller_src
    assert "@Post('issue')" in controller_src or '@Post("issue")' in controller_src
    assert "@Post('verify')" in controller_src or '@Post("verify")' in controller_src

    module_src = module_file.read_text()
    assert "@Module" in module_src
    assert "ApiKeysController" in module_src

    service_src = service_file.read_text()
    assert "class ApiKeysService" in service_src


def test_core_files_exist(module_root: Path) -> None:
    expected = [
        "module.yaml",
        "generate.py",
        "overrides.py",
        "config/base.yaml",
        "config/snippets.yaml",
        "module.verify.json",
        ".module_state.json",
    ]
    for rel_path in expected:
        assert (module_root / rel_path).exists(), rel_path


def test_framework_files_exist(module_root: Path) -> None:
    expected = [
        "frameworks/fastapi.py",
        "frameworks/nestjs.py",
    ]
    for rel_path in expected:
        assert (module_root / rel_path).exists(), rel_path


def test_templates_exist(module_root: Path) -> None:
    expected = [
        "templates/base/api_keys.py.j2",
        "templates/base/api_keys_health.py.j2",
        "templates/base/api_keys_types.py.j2",
        "templates/variants/fastapi/api_keys.py.j2",
        "templates/variants/fastapi/api_keys_routes.py.j2",
        "templates/variants/fastapi/api_keys_health.py.j2",
        "templates/variants/nestjs/api_keys.service.ts.j2",
        "templates/variants/nestjs/api_keys.controller.ts.j2",
        "templates/variants/nestjs/api_keys.module.ts.j2",
        "templates/vendor/nestjs/configuration.js.j2",
    ]
    for rel_path in expected:
        assert (module_root / rel_path).exists(), rel_path
