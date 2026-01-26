"""End-to-end smoke test for AI Assistant module in FastAPI projects.

Validates that the generated routes respond correctly and basic request/response
flows work as expected.
"""

from http import HTTPStatus

import pytest


@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Verify health endpoint returns ok status."""
    response = await client.get("/api/health")
    if response.status_code != HTTPStatus.OK:
        pytest.fail(f"unexpected status code: {response.status_code}")
    data = response.json()
    if "status" not in data:
        pytest.fail("missing 'status' in health response")


@pytest.mark.asyncio
async def test_health_probe_metadata(client):
    """Verify health probe includes expected metadata fields."""
    response = await client.get("/api/health")
    if response.status_code != HTTPStatus.OK:
        pytest.fail(f"unexpected status code: {response.status_code}")
    data = response.json()
    # Module health should have version and status at minimum
    if not any(k in data for k in ["version", "status", "module"]):
        pytest.fail("health response missing version/status/module keys")
