"""Health helper tests for Security Headers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import pytest

from tests.modules.free.security.security_headers.conftest import (
    load_module_from_path,
    prepare_vendor_package,
)


@pytest.fixture()
def health_module(
    tmp_path: Path,
    module_generate,  # type: ignore[annotation-unchecked]
    module_config: Mapping[str, Any],
):
    renderer = module_generate.TemplateRenderer()
    context = module_generate.build_base_context(module_config)
    module_generate.generate_vendor_files(module_config, tmp_path, renderer, context)

    vendor_base = tmp_path / ".rapidkit" / "vendor"
    prepare_vendor_package(vendor_base, context)
    version_dir = (
        vendor_base / context["rapidkit_vendor_module"] / context["rapidkit_vendor_version"]
    )
    runtime_path = version_dir / context["rapidkit_vendor_relative_path"]
    health_helpers = load_module_from_path(
        version_dir / "src/health/security_headers.py",
        "tests_security.security_headers_health",
    )
    runtime_module = load_module_from_path(
        runtime_path,
        "tests_security.security_headers_vendor",
    )
    return runtime_module, health_helpers


def test_health_payload_contains_metrics(health_module) -> None:
    runtime_module, _ = health_module
    runtime = runtime_module.SecurityHeaders()
    payload = runtime.health_check()
    assert payload["module"] == "security_headers"
    assert payload["metrics"]["missing"] == []


def test_health_detects_missing_headers(health_module) -> None:
    runtime_module, health_helpers = health_module
    cfg = runtime_module.SecurityHeadersConfig()
    runtime = runtime_module.SecurityHeaders(cfg)
    headers = runtime.headers(refresh=True)
    headers.pop("Cross-Origin-Opener-Policy", None)
    metrics = health_helpers.evaluate_completeness(cfg, headers)
    assert "Cross-Origin-Opener-Policy" in metrics.missing
