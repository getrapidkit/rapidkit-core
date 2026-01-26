"""Unit tests for the storage health helper."""

from __future__ import annotations

import pytest

from modules.free.business.storage import generate


@pytest.mark.asyncio
async def test_health_helper_uses_runtime(rendered_storage_health, storage_config):
    health_check = rendered_storage_health.health_check
    result = await health_check(storage_config)
    assert result["module"] == generate.MODULE_NAME
    assert result["adapter"]["adapter"] == "local"
