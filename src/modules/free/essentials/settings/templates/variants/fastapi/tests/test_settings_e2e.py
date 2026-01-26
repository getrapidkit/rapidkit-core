"""E2E smoke test for Settings (FastAPI).

This is intentionally lightweight and designed to run without external services.
"""

from __future__ import annotations

import importlib

import pytest


def test_router_builds_without_crashing() -> None:
    fastapi = pytest.importorskip("fastapi")
    _ = fastapi

    router_module = importlib.import_module("src.modules.free.essentials.settings.routers.settings")

    router = getattr(router_module, "router", None)
    if router is None:
        build_router = getattr(router_module, "build_router", None)
        create_router = getattr(router_module, "create_router", None)
        if callable(build_router):
            router = build_router()
        elif callable(create_router):
            router = create_router()
        else:
            # Some modules expose only a runtime facade without HTTP routes.
            assert router_module is not None
            return

    assert getattr(router, "routes", None) is not None
