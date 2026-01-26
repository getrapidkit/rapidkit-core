"""Generator level tests for the storage module."""

from __future__ import annotations

from pathlib import Path

import pytest

from modules.free.business.storage import generate


def test_module_yaml_exists(storage_module_path: Path) -> None:
    assert (storage_module_path / "module.yaml").exists()


def test_generate_py_exists(storage_module_path: Path) -> None:
    assert (storage_module_path / "generate.py").exists()


def test_overrides_py_exists(storage_module_path: Path) -> None:
    assert (storage_module_path / "overrides.py").exists()


def test_frameworks_exist(storage_module_path: Path) -> None:
    assert (storage_module_path / "frameworks/fastapi.py").exists()
    assert (storage_module_path / "frameworks/nestjs.py").exists()


def test_templates_exist(storage_module_path: Path) -> None:
    assert (storage_module_path / "templates/base").exists()
    assert (storage_module_path / "templates/variants/fastapi").exists()
    assert (storage_module_path / "templates/variants/nestjs").exists()


def test_config_files_exist(storage_module_path: Path) -> None:
    assert (storage_module_path / "config/base.yaml").exists()
    assert (storage_module_path / "config/snippets.yaml").exists()


def test_storage_template_renders_class_definition() -> None:
    renderer = generate.TemplateRenderer()
    config = generate.load_module_config()
    context = generate.build_base_context(config)
    template = generate.MODULE_ROOT / "templates/base/storage.py.j2"

    rendered = renderer.render(template, context)
    assert "class FileStorage" in rendered


def test_generate_variants_produce_expected_outputs(tmp_path: Path) -> None:
    config = generate.load_module_config()
    context = generate.build_base_context(config)
    renderer = generate.TemplateRenderer()
    if getattr(renderer, "_env", None) is None:
        pytest.skip("jinja2 is required to render Storage templates")

    generate.generate_vendor_files(config, tmp_path, renderer, context)
    vendor_root = (
        tmp_path
        / ".rapidkit"
        / "vendor"
        / context["rapidkit_vendor_module"]
        / context["rapidkit_vendor_version"]
    )
    vendor_expected = {
        vendor_root / "src" / "modules" / "free" / "business" / "storage" / "storage.py",
        vendor_root / "src" / "health" / "storage.py",
        vendor_root / "src" / "modules" / "free" / "business" / "storage" / "types" / "storage.py",
        vendor_root / "nestjs" / "configuration.js",
    }
    for artefact in vendor_expected:
        assert artefact.exists(), f"Expected vendor artefact {artefact}"
        assert artefact.read_text().strip(), f"Generated vendor file {artefact} is empty"

    generate.generate_variant_files(config, "fastapi", tmp_path, renderer, context)
    fastapi_expected = {
        tmp_path / "src" / "modules" / "free" / "business" / "storage" / "storage.py",
        tmp_path / "src" / "modules" / "free" / "business" / "storage" / "routers" / "storage.py",
        tmp_path / "config" / "storage.yaml",
        tmp_path
        / "tests"
        / "modules"
        / "integration"
        / "business"
        / "storage"
        / "test_storage_integration.py",
    }

    # Accept either the legacy project-level health runtime or the canonical
    # vendor-backed health placement under src/health.
    health_candidates = [
        tmp_path / "src" / "health" / "storage.py",
        tmp_path / "src" / "core" / "health" / "storage.py",
    ]
    assert any(
        p.exists() for p in health_candidates
    ), "Expected one of the canonical health artefacts to exist"
    # Validate the other required artefacts
    for artefact in fastapi_expected:
        assert artefact.exists(), f"Expected FastAPI artefact {artefact}"
        assert artefact.read_text().strip(), f"Generated FastAPI file {artefact} is empty"

    router_src = (
        tmp_path / "src" / "modules" / "free" / "business" / "storage" / "routers" / "storage.py"
    ).read_text()
    assert any(
        token in router_src
        for token in (
            'APIRouter(prefix="/api/v1/storage"',
            "APIRouter(prefix='/api/v1/storage'",
        )
    ), "FastAPI router should expose /api/v1/storage namespace"
    assert any(
        token in router_src
        for token in (
            "@router.post('/upload'",
            '@router.post("/upload"',
        )
    ), "FastAPI router should expose upload endpoint"
    assert any(
        token in router_src
        for token in (
            "@router.get('/{file_id}'",
            '@router.get("/{file_id}"',
        )
    ), "FastAPI router should expose download endpoint"
    assert any(
        token in router_src
        for token in (
            "@router.delete('/{file_id}'",
            '@router.delete("/{file_id}"',
        )
    ), "FastAPI router should expose delete endpoint"
    assert any(
        token in router_src
        for token in (
            "@router.get('/health/status'",
            '@router.get("/health/status"',
        )
    ), "FastAPI router should expose health endpoint"

    generate.generate_variant_files(config, "nestjs", tmp_path, renderer, context)
    storage_dir = tmp_path / "src" / "modules" / "free" / "business" / "storage"
    nest_expected = {
        storage_dir / "storage.service.ts",
        storage_dir / "storage.controller.ts",
        storage_dir / "storage.module.ts",
        storage_dir / "storage.health.ts",
        storage_dir / "storage.routes.ts",
        storage_dir / "storage.configuration.ts",
    }
    for artefact in nest_expected:
        assert artefact.exists(), f"Expected NestJS artefact {artefact}"
        assert artefact.read_text().strip(), f"Generated NestJS file {artefact} is empty"

    nest_tests = (
        tmp_path
        / "tests"
        / "modules"
        / "integration"
        / "business"
        / "storage"
        / "storage.integration.spec.ts"
    )
    assert nest_tests.exists(), "Expected NestJS integration spec to be generated"
    assert nest_tests.read_text().strip(), "Generated NestJS integration spec is empty"

    controller_src = (storage_dir / "storage.controller.ts").read_text()
    assert (
        "@Controller('api/v1/storage')" in controller_src
        or '@Controller("api/v1/storage")' in controller_src
    ), "Storage controller should mount api/v1/storage routes"
    assert "@Post('upload')" in controller_src or '@Post("upload")' in controller_src
    assert "@Get(':id')" in controller_src or '@Get(":id")' in controller_src
    assert "@Delete(':id')" in controller_src or '@Delete(":id")' in controller_src
    assert (
        "@Get('health/status')" in controller_src or '@Get("health/status")' in controller_src
    ), "Storage controller should expose health endpoint"

    module_src = (storage_dir / "storage.module.ts").read_text()
    assert "StorageModule" in module_src
    assert "StorageService" in module_src
    assert "StorageController" in module_src
    assert "MulterModule.register" in module_src

    service_src = (storage_dir / "storage.service.ts").read_text()
    assert "async uploadFile" in service_src
    assert "async downloadFile" in service_src
    assert "async deleteFile" in service_src
    assert "async healthCheck" in service_src

    health_src = (storage_dir / "storage.health.ts").read_text()
    assert "StorageHealthController" in health_src

    routes_src = (storage_dir / "storage.routes.ts").read_text()
    assert "STORAGE_ROUTES" in routes_src
