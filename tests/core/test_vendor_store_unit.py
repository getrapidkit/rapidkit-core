from pathlib import Path

from core.services import vendor_store


def test_vendor_file_path(tmp_path):
    root = tmp_path
    target = vendor_store.vendor_file_path(root, "module/path", "1.0.0", "file.txt")
    assert target == root / vendor_store.VENDOR_DIR / "module" / "path" / "1.0.0" / "file.txt"


def test_store_and_load_vendor_file(tmp_path):
    root = tmp_path
    stored_path = vendor_store.store_vendor_file(
        root,
        module="example/module",
        version="2.3.4",
        rel_path="data.json",
        content=b"{}",
    )
    assert stored_path.exists()

    loaded = vendor_store.load_vendor_file(root, "example/module", "2.3.4", "data.json")
    assert loaded == b"{}"


def test_load_vendor_file_missing(tmp_path):
    root = tmp_path
    assert vendor_store.load_vendor_file(root, None, "1.0.0", "missing.txt") is None
    assert vendor_store.load_vendor_file(root, "mod", "1.0.0", "missing.txt") is None


def test_load_vendor_file_handles_oserror(tmp_path, monkeypatch):
    root = tmp_path
    vendor_store.store_vendor_file(
        root,
        module="example/module",
        version="2.3.4",
        rel_path="data.json",
        content=b"{}",
    )

    def broken_read_bytes(_self):
        raise OSError("boom")

    monkeypatch.setattr(Path, "read_bytes", broken_read_bytes)

    assert vendor_store.load_vendor_file(root, "example/module", "2.3.4", "data.json") is None
