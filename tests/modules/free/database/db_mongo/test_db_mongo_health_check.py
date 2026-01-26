"""Vendor health helper tests for Db Mongo."""

from __future__ import annotations

import pytest

from .test_db_mongo_runtime import _StubClient


@pytest.mark.asyncio()
async def test_health_helper_reports_metrics(generated_db_mongo_modules) -> None:
    health_module = generated_db_mongo_modules.health
    base_module = generated_db_mongo_modules.base

    stub_client = _StubClient()
    runtime = base_module.DbMongo(client_factory=lambda config: stub_client)

    report = await health_module.perform_health_check(runtime, timeout_ms=200, collect_metrics=True)

    assert report.status in {"ok", "degraded", "critical"}
    assert isinstance(report.metrics.latency_ms, float)
    payload = report.to_payload()
    assert "metrics" in payload
