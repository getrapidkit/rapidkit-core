"""Runtime behaviour tests for the Db Mongo vendor payload."""

from __future__ import annotations

import pytest


class _StubAdminDatabase:
    def __init__(self, parent: "_StubClient") -> None:
        self._parent = parent

    async def command(self, payload, **kwargs):  # type: ignore[override]
        self._parent.last_command = payload
        return {"ok": 1, "payload": payload, "kwargs": kwargs}


class _StubClient:
    def __init__(self) -> None:
        self.admin = _StubAdminDatabase(self)
        self.closed = False
        self.last_command = None

    def get_database(self, name: str):  # type: ignore[override]
        if name == "admin":
            return self.admin
        return self

    def get_collection(self, name: str):  # pragma: no cover - not used in tests
        return {"name": name}

    async def server_info(self):  # type: ignore[override]
        return {
            "version": "7.0.0",
            "connections": {"current": 5},
            "opcounters": {"query": 10},
            "wiredTiger": {"cache": {"bytes currently in the cache": 1024}},
        }

    def close(self) -> None:  # type: ignore[override]
        self.closed = True


@pytest.mark.asyncio()
async def test_runtime_health_check_with_stub_client(generated_db_mongo_modules) -> None:
    runtime_module = generated_db_mongo_modules.base
    stub_client = _StubClient()

    runtime = runtime_module.DbMongo(client_factory=lambda config: stub_client)
    report = await runtime.health_check(timeout_ms=100)

    assert report.status == "ok"
    assert report.metrics.latency_ms >= 0
    payload = report.to_payload()
    assert payload["module"] == "db_mongo"
    assert stub_client.last_command == {"ping": 1, "$db": "admin"}

    await runtime.close()
    assert stub_client.closed is True


@pytest.mark.asyncio()
async def test_server_info_pass_through(generated_db_mongo_modules) -> None:
    runtime_module = generated_db_mongo_modules.base
    stub_client = _StubClient()

    runtime = runtime_module.DbMongo(client_factory=lambda config: stub_client)
    info = await runtime.server_info()

    assert info["version"] == "7.0.0"
    metadata = runtime.metadata()
    assert metadata["config"]["pool"]["max"] == runtime.config.max_pool_size
    await runtime.close()
