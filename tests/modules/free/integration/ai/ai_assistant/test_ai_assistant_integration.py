from pathlib import Path


def test_free_ai_ai_assistant_integration_placeholder() -> None:
    """Validate that the generated module runtime exists within the repository."""

    repo_root = Path(__file__).resolve().parents[6]
    module_paths = [
        repo_root / "modules/free/ai/ai_assistant",
        repo_root / "src/modules/free/ai/ai_assistant",
    ]
    assert any(
        path.exists() for path in module_paths
    ), "Generated module runtime path should exist before running integration tests"
