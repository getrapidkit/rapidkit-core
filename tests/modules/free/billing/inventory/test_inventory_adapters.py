"""Framework adapter tests for the Inventory module."""

from __future__ import annotations

import pytest

httpx = pytest.importorskip("httpx")


@pytest.mark.parametrize("endpoint", ["/inventory/health", "/inventory/items"])
@pytest.mark.asyncio
async def test_fastapi_routes_exposed(fastapi_import_path, endpoint: str) -> None:
    fastapi = pytest.importorskip("fastapi")

    from src.modules.free.billing.inventory.inventory import InventoryService, register_fastapi

    app = fastapi.FastAPI()
    service = InventoryService()
    service.upsert_item(sku="sku-10", name="Adapter", quantity=2, price="4.00")
    register_fastapi(app, service=service)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(endpoint)
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_fastapi_adjust_endpoint_handles_errors(fastapi_import_path) -> None:
    fastapi = pytest.importorskip("fastapi")

    from src.modules.free.billing.inventory.inventory import InventoryService, register_fastapi

    app = fastapi.FastAPI()
    service = InventoryService()
    service.upsert_item(sku="sku-err", name="Error Case", quantity=1, price="3.00")
    register_fastapi(app, service=service)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/inventory/items/sku-err/adjust", json={"delta": -5})
        assert response.status_code == 422
