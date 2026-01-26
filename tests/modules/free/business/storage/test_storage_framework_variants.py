"""Tests for framework-specific templates."""

from __future__ import annotations

from pathlib import Path


def test_fastapi_variant_defines_routes(storage_module_path: Path) -> None:
    template = (storage_module_path / "templates/variants/fastapi/storage_routes.py.j2").read_text(
        encoding="utf-8"
    )
    assert "@router.post" in template
    assert "get_storage" in template


def test_fastapi_variant_provides_config_template(storage_module_path: Path) -> None:
    template = (
        storage_module_path / "templates/variants/fastapi/storage_config.yaml.j2"
    ).read_text(encoding="utf-8")
    assert "storage:" in template
    assert "logging:" in template


def test_nestjs_service_exposes_methods(storage_module_path: Path) -> None:
    template = (storage_module_path / "templates/variants/nestjs/storage.service.ts.j2").read_text(
        encoding="utf-8"
    )
    assert "uploadFile" in template
    assert "downloadFile" in template
    assert "healthCheck" in template


def test_variants_reference_same_service(storage_module_path: Path) -> None:
    controller = (
        storage_module_path / "templates/variants/nestjs/storage.controller.ts.j2"
    ).read_text(encoding="utf-8")
    assert "{{ module_service_class }}" in controller


def test_nestjs_variant_exposes_health_and_routes(storage_module_path: Path) -> None:
    health = (storage_module_path / "templates/variants/nestjs/storage.health.ts.j2").read_text(
        encoding="utf-8"
    )
    routes = (storage_module_path / "templates/variants/nestjs/storage.routes.ts.j2").read_text(
        encoding="utf-8"
    )
    assert "StorageHealthController" in health
    assert "STORAGE_ROUTES" in routes
