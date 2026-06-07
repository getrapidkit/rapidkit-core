import pytest

httpx = pytest.importorskip("httpx")
pytest.importorskip("fastapi")

from fastapi import FastAPI  # noqa: E402


@pytest.mark.asyncio
async def test_fastapi_adapter_exposes_completion(rendered_llm_gateway) -> None:  # type: ignore[no-untyped-def]
    runtime = rendered_llm_gateway["runtime"]

    app = FastAPI()
    app.include_router(runtime.create_router())

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        health = await client.get("/llm-gateway/health")
        completion = await client.post(
            "/llm-gateway/complete",
            json={"prompt": "route this request", "tenant_id": "tenant-1"},
        )

    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert completion.status_code == 200
    assert completion.json()["provider"] == "local"
    assert completion.json()["estimated_tokens"] > 0
