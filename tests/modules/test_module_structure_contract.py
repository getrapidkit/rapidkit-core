from __future__ import annotations

from core.services.module_structure_validator import validate_modules


def test_all_modules_match_structure_spec() -> None:
    results = validate_modules()
    failures = [result for result in results if not result.valid]
    if not failures:
        return

    details = []
    for failure in failures:
        messages = failure.messages or ["No diagnostic messages were provided."]
        combined = "\n    ".join(messages)
        details.append(f"- {failure.module}:\n    {combined}")

    joined = "\n".join(details)
    raise AssertionError(
        "Module structure spec violations detected.\n"
        "Run 'poetry run python scripts/validate_module_structure.py' for a detailed report.\n"
        f"{joined}"
    )
