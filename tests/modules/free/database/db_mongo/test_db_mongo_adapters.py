"""Framework integration tests for Db Mongo."""

from __future__ import annotations

import pytest

httpx = pytest.importorskip("httpx")

from fastapi import FastAPI  # noqa: E402

from .test_db_mongo_runtime import _StubClient  # noqa: E402


@pytest.mark.asyncio
async def test_fastapi_routes_expose_health_and_info(generated_db_mongo_modules) -> None:
    runtime_module = generated_db_mongo_modules.fastapi_runtime
    stub_client = _StubClient()

    app = FastAPI()
    runtime = runtime_module.DbMongo(client_factory=lambda config: stub_client)
    runtime_module.register_fastapi(app, runtime=runtime)

    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/db-mongo/health")
        assert response.status_code == 200
        payload = response.json()
        assert payload["module"] == "db_mongo"
        assert payload["status"] in {"ok", "degraded", "critical"}

        info_response = await client.get("/db-mongo/info")
        assert info_response.status_code == 200
        info_payload = info_response.json()
        assert info_payload["module"] == "db_mongo"
        assert "info" in info_payload
