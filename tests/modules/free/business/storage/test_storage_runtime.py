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
