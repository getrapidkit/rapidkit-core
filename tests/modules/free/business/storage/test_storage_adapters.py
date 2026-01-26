"""Low-level adapter tests for the Storage module."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_local_adapter_roundtrip(rendered_storage_runtime, tmp_path):
    StorageConfig = rendered_storage_runtime.StorageConfig
    adapter_cls = rendered_storage_runtime.LocalStorageAdapter

    adapter = adapter_cls(StorageConfig(base_path=tmp_path))

    await adapter.save("sample.txt", b"payload")
    metadata = await adapter.stat("sample.txt")
    assert metadata.size == len(b"payload")

    payload = await adapter.load("sample.txt")
    assert payload == b"payload"

    health = await adapter.health()
    assert health["adapter"] == "local"
    assert health["writable"] is True

    await adapter.delete("sample.txt")
    with pytest.raises(FileNotFoundError):
        await adapter.load("sample.txt")
