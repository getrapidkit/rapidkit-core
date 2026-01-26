"""Error handling tests for the storage runtime."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_download_missing_file_raises(storage_facade):
    with pytest.raises(FileNotFoundError):
        await storage_facade.download_file("unknown.txt")


def test_unsupported_adapter_configuration(rendered_storage_runtime, tmp_path):
    StorageConfig = rendered_storage_runtime.StorageConfig
    UnsupportedAdapterError = rendered_storage_runtime.UnsupportedAdapterError
    storage_cls = rendered_storage_runtime.FileStorage

    config = StorageConfig(base_path=tmp_path, adapter="s3")

    with pytest.raises(UnsupportedAdapterError):
        storage_cls(config)
