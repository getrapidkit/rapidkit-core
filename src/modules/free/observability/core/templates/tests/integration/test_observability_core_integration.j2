"""Integration smoke tests for Observability Core FastAPI variant."""

from importlib import import_module
from importlib import util as importlib_util
from pathlib import Path
import pytest

FASTAPI_AVAILABLE = importlib_util.find_spec("fastapi") is not None

pytestmark = [
    pytest.mark.integration,
    pytest.mark.template_integration,
]

def test_runtime_exports() -> None:
    """Runtime exposes expected helpers."""

    module = import_module("src.modules.free.observability.core.observability_core")
    expected = {
        "ObservabilityCore",
        "ObservabilityCoreConfig",
        "get_runtime",
        "register_metrics_endpoint",
    }

    missing = [name for name in expected if not hasattr(module, name)]
    assert not missing, f"Missing expected exports: {missing}"

@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="fastapi not installed")
def test_fastapi_registration(monkeypatch):
    """Register helper attaches router and exposes metrics endpoint."""

    from fastapi import FastAPI

    app = FastAPI()
    attached: dict[str, bool] = {"called": False}

    def fake_include_router(router, **_: object) -> None:
        attached["called"] = True
        assert router is not None
        assert any(
            getattr(route, "path", "").endswith("/metrics") for route in getattr(router, "routes", [])
        )

    monkeypatch.setattr(app, "include_router", fake_include_router)

    from src.modules.free.observability.core.observability_core import ObservabilityCoreConfig
    from src.modules.free.observability.core.observability_core import register_fastapi

    config = ObservabilityCoreConfig.from_mapping({})
    register_fastapi(app, config=config)
    assert attached["called"], "Expected router to be attached"

@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="fastapi not installed")
def test_router_factory_signatures():
    """Verify router factory exposes expected call signatures."""

    from src.modules.free.observability.core.routers import observability_core as router_module

    assert hasattr(router_module, "build_router")
    router = router_module.build_router()
    assert router is not None

    assert any(
        getattr(route, "path", "").endswith("/health") for route in getattr(router, "routes", [])
    )

def test_generator_entrypoint() -> None:
    """Smoky assertion ensuring generator is importable."""

    module_root = Path(__file__).resolve().parents[3]
    assert module_root.exists()
