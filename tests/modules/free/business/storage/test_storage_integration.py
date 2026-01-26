from pathlib import Path


def test_free_business_storage_integration_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[5]
    module_path = repo_root / "src/modules/free/business/storage"
    assert module_path.exists()
