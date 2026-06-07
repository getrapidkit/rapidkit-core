"""Runtime behaviour tests for the Storage module."""

from __future__ import annotations

import pytest

from modules.free.business.storage import generate


@pytest.mark.asyncio
async def test_upload_download_delete_cycle(storage_facade, tmp_path):
    payload = b"hello rapidkit"
    result = await storage_facade.upload_file("greeting.txt", payload)

    assert result.success is True
    assert result.file_id is not None
    stored_path = tmp_path / result.file_id
    assert stored_path.exists()
    stored = await storage_facade.download_file(result.file_id)
    assert stored == payload

    metadata = await storage_facade.get_file_info(result.file_id)
    assert metadata.extra["original_filename"] == "greeting.txt"
    assert metadata.checksum is not None

    await storage_facade.delete_file(result.file_id)
    with pytest.raises(FileNotFoundError):
        await storage_facade.download_file(result.file_id)
    assert stored_path.exists() is False


@pytest.mark.asyncio
async def test_health_check_reports_local_status(storage_facade, tmp_path):
    health = await storage_facade.health_check()
    assert health["module"] == generate.MODULE_NAME
    adapter = health["adapter"]
    assert adapter["adapter"] == "local"
    assert adapter["path"] == str(tmp_path)


@pytest.mark.asyncio
async def test_signed_download_token_and_checksum(storage_facade):
    payload = b"receipt artifact"
    result = await storage_facade.upload_file("receipt.pdf", payload)

    assert result.file_id is not None
    assert await storage_facade.verify_checksum(result.file_id, result.metadata.checksum)

    token = storage_facade.create_download_token(result.file_id)
    resolved_file_id = storage_facade.verify_download_token(token)

    assert resolved_file_id == result.file_id


@pytest.mark.asyncio
async def test_malware_scan_hook_blocks_payload(rendered_storage_runtime, tmp_path):
    StorageConfig = rendered_storage_runtime.StorageConfig
    Storage = getattr(rendered_storage_runtime, generate.MODULE_CLASS)
    FileValidationError = rendered_storage_runtime.FileValidationError

    config = StorageConfig(base_path=tmp_path, malware_scan_hook=lambda _name, _body: False)
    storage = Storage(config)

    with pytest.raises(FileValidationError, match="malware scan"):
        await storage.upload_file("blocked.txt", b"bad")
