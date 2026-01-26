from pathlib import Path

import pytest


@pytest.fixture(name="module_test_context")
def module_test_context_fixture(tmp_path: Path) -> dict[str, object]:
    """Provide an isolated workspace for Ai Assistant module tests."""

    working_dir = tmp_path / "ai_assistant"
    working_dir.mkdir(parents=True, exist_ok=True)
    return {
        "module_name": "ai_assistant",
        "workspace": working_dir,
        "context_file": working_dir / "context.json",
    }
