from pathlib import Path


def test_free_communication_email_integration_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[5]
    module_path = repo_root / "src/modules/free/communication/email"
    assert module_path.exists()
