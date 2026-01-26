import importlib
import sys
from types import ModuleType, SimpleNamespace

import pytest

fastapi = pytest.importorskip("fastapi")
FastAPI = fastapi.FastAPI


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def postgres_health_module():
    inserted_modules: list[str] = []

    if "runtime.core.database.postgres" not in sys.modules:
        stub = ModuleType("runtime.core.database.postgres")

        async def _check_postgres_connection():
            return None

        async def _get_pool_status():
            return {}

        def _get_database_url(*_, **__):
            return "postgresql://stub"

        stub.check_postgres_connection = _check_postgres_connection
        stub.get_pool_status = _get_pool_status
        stub.get_database_url = _get_database_url
        sys.modules["runtime.core.database.postgres"] = stub
        inserted_modules.append("runtime.core.database.postgres")

    if "core.settings" not in sys.modules:
        settings_stub = ModuleType("core.settings")
        settings_stub.settings = SimpleNamespace(
            DATABASE_URL="postgresql://stub",
            DB_ECHO=False,
            DB_POOL_SIZE=1,
            DB_MAX_OVERFLOW=1,
            DB_POOL_RECYCLE=300,
            DB_POOL_TIMEOUT=30,
            TEST_DATABASE_URL=None,
        )
        sys.modules["core.settings"] = settings_stub
        inserted_modules.append("core.settings")

    module = importlib.import_module("runtime.core.health.database.postgres")
    loaded = importlib.reload(module)

    yield loaded

    for name in inserted_modules:
        sys.modules.pop(name, None)


@pytest.mark.anyio
async def test_postgres_health_check_returns_payload(monkeypatch, postgres_health_module):
    calls = {"check": False, "debug": []}

    async def fake_check_postgres_connection():
        calls["check"] = True

    async def fake_get_pool_status():
        return {"size": 3, "available": 2}

    def fake_get_database_url(hide_password):
        assert hide_password is True
        return "postgresql://user:***@localhost/db"

    class DummyLogger:
        def debug(self, message, *, extra):
            calls["debug"].append((message, extra))

    monkeypatch.setattr(
        postgres_health_module,
        "check_postgres_connection",
        fake_check_postgres_connection,
    )
    monkeypatch.setattr(postgres_health_module, "get_pool_status", fake_get_pool_status)
    monkeypatch.setattr(postgres_health_module, "get_database_url", fake_get_database_url)
    monkeypatch.setattr(postgres_health_module.platform, "node", lambda: "health-host")
    monkeypatch.setattr(postgres_health_module, "logger", DummyLogger())

    result = await postgres_health_module.postgres_health_check()

    assert calls["check"] is True
    assert result == {
        "status": "ok",
        "module": "db_postgres",
        "url": "postgresql://user:***@localhost/db",
        "hostname": "health-host",
        "pool": {"size": 3, "available": 2},
    }
    assert calls["debug"] == [
        (
            "PostgreSQL health probe succeeded",
            {"pool": {"size": 3, "available": 2}},
        )
    ]


def test_register_postgres_health_mounts_router(postgres_health_module):
    app = FastAPI()
    importlib.reload(postgres_health_module)

    postgres_health_module.register_postgres_health(app)

    paths = {route.path for route in app.routes}
    assert "/api/health/module/postgres" in paths


def test_register_postgres_health_requires_fastapi(monkeypatch, postgres_health_module):
    monkeypatch.setattr(postgres_health_module, "_FASTAPI_AVAILABLE", False)
    with pytest.raises(RuntimeError):
        postgres_health_module.register_postgres_health(object())
