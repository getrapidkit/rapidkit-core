"""Runtime behaviour tests for the Security Headers vendor payload."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import pytest

from .conftest import load_module_from_path, prepare_vendor_package


@pytest.fixture()
def vendor_module(
    tmp_path: Path,
    module_generate,  # type: ignore[annotation-unchecked]
    module_config: Mapping[str, Any],
):
    renderer = module_generate.TemplateRenderer()
    context = module_generate.build_base_context(module_config)
    module_generate.generate_vendor_files(module_config, tmp_path, renderer, context)

    vendor_base = tmp_path / ".rapidkit" / "vendor"
    prepare_vendor_package(vendor_base, context)
    vendor_file = (
        vendor_base
        / context["rapidkit_vendor_module"]
        / context["rapidkit_vendor_version"]
        / context["rapidkit_vendor_relative_path"]
    )
    return load_module_from_path(vendor_file, "tests_security.security_headers_vendor")


def test_default_headers_cover_recommended_set(vendor_module) -> None:
    runtime = vendor_module.SecurityHeaders()
    headers = runtime.headers()
    for header_name in [
        "Strict-Transport-Security",
        "X-Content-Type-Options",
        "X-Frame-Options",
        "Referrer-Policy",
    ]:
        assert header_name in headers


def test_runtime_respects_configuration_toggles(vendor_module) -> None:
    cfg = vendor_module.SecurityHeadersConfig(
        strict_transport_security=False,
        permissions_policy={"geolocation": None},
    )
    runtime = vendor_module.SecurityHeaders(cfg)
    headers = runtime.headers(refresh=True)
    assert "Strict-Transport-Security" not in headers
    assert headers["Permissions-Policy"] == "geolocation=()"


def test_apply_merges_headers(vendor_module) -> None:
    runtime = vendor_module.SecurityHeaders()
    target: dict[str, str] = {"Existing": "value"}
    applied = runtime.apply(target)
    assert target["Existing"] == "value"
    assert applied["X-Content-Type-Options"] == "nosniff"
    assert "X-Content-Type-Options" in target
