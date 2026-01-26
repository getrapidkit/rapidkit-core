"""Validation tests for the Storage runtime."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_rejects_disallowed_extension(rendered_storage_runtime, tmp_path):
    StorageConfig = rendered_storage_runtime.StorageConfig
    FileValidationError = rendered_storage_runtime.FileValidationError
    storage_cls = rendered_storage_runtime.FileStorage

    config = StorageConfig(base_path=tmp_path, allowed_extensions=("txt",))
    storage = storage_cls(config)

    with pytest.raises(FileValidationError):
        await storage.upload_file("image.png", b"data")


@pytest.mark.asyncio
async def test_rejects_oversized_payload(rendered_storage_runtime, tmp_path):
    StorageConfig = rendered_storage_runtime.StorageConfig
    FileValidationError = rendered_storage_runtime.FileValidationError
    storage_cls = rendered_storage_runtime.FileStorage

    config = StorageConfig(base_path=tmp_path, max_file_size=4)
    storage = storage_cls(config)

    with pytest.raises(FileValidationError):
        await storage.upload_file("clip.txt", b"exceeds")
