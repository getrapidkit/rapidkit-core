"""E2E smoke test for Document Pipeline (FastAPI).

This is intentionally lightweight and designed to run without external services.
"""

from __future__ import annotations

import importlib

import pytest


def test_router_builds_without_crashing() -> None:
    fastapi = pytest.importorskip("fastapi")
    _ = fastapi

    router_rel = "src/modules/free/business/document_pipeline/routers/business/document_pipeline.py"
    router_mod_path = router_rel.replace("/", ".").removesuffix(".py")
    router_module = importlib.import_module(router_mod_path)

    router = getattr(router_module, "router", None)
    if router is None:
        build_router = getattr(router_module, "build_router", None)
        create_router = getattr(router_module, "create_router", None)
        if callable(build_router):
            router = build_router()
        elif callable(create_router):
            router = create_router()
        else:
            pytest.skip("Module router does not expose router/build_router/create_router")

    assert getattr(router, "routes", None) is not None
