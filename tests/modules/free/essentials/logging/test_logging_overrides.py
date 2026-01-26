from pathlib import Path

import pytest

from modules.free.essentials.logging.overrides import LoggingOverrides


@pytest.fixture
def base_context() -> dict[str, object]:
    return {
        "logging_defaults": {
            "level": "INFO",
            "format": "json",
            "sinks": ["stderr"],
            "async_queue": True,
            "file_path": "logs/app.log",
            "sampling_rate": 1.0,
            "enable_redaction": True,
            "otel_bridge_enabled": False,
            "metrics_bridge_enabled": False,
        },
        "logging_request_context_enabled": True,
    }


def test_overrides_mutate_defaults_and_copy_snippet(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, base_context: dict[str, object]
) -> None:
    snippet = tmp_path / "logging-extra.md"
    snippet.write_text("extra snippet", encoding="utf-8")

    monkeypatch.setenv("RAPIDKIT_LOGGING_FORCE_LEVEL", "debug")
    monkeypatch.setenv("RAPIDKIT_LOGGING_FORCE_FORMAT", "colored")
    monkeypatch.setenv("RAPIDKIT_LOGGING_FORCE_SINKS", '["stderr","file"]')
    monkeypatch.setenv("RAPIDKIT_LOGGING_FORCE_ASYNC_QUEUE", "false")
    monkeypatch.setenv("RAPIDKIT_LOGGING_FORCE_FILE_PATH", "var/log/app.log")
    monkeypatch.setenv("RAPIDKIT_LOGGING_FORCE_SAMPLING", "0.5")
    monkeypatch.setenv("RAPIDKIT_LOGGING_FORCE_REDACTION", "false")
    monkeypatch.setenv("RAPIDKIT_LOGGING_FORCE_OTEL", "true")
    monkeypatch.setenv("RAPIDKIT_LOGGING_FORCE_METRICS", "true")
    monkeypatch.setenv("RAPIDKIT_LOGGING_DISABLE_REQUEST_CONTEXT", "true")
    monkeypatch.setenv("RAPIDKIT_LOGGING_EXTRA_SNIPPET", str(snippet))
    monkeypatch.setenv("RAPIDKIT_LOGGING_EXTRA_SNIPPET_DEST", "config/logging-extra.md")

    overrides = LoggingOverrides()
    mutated = overrides.apply_base_context(base_context)

    defaults = mutated["logging_defaults"]  # type: ignore[index]
    assert defaults["level"] == "DEBUG"
    assert defaults["format"] == "colored"
    assert defaults["sinks"] == ["stderr", "file"]
    assert defaults["async_queue"] is False
    assert defaults["file_path"] == "var/log/app.log"
    expected_sampling = 0.5
    assert defaults["sampling_rate"] == expected_sampling
    assert defaults["enable_redaction"] is False
    assert defaults["otel_bridge_enabled"] is True
    assert defaults["metrics_bridge_enabled"] is True
    assert mutated["logging_request_context_enabled"] is False

    target_dir = tmp_path / "project"
    target_dir.mkdir()
    overrides.post_variant_generation(
        variant_name="fastapi",
        target_dir=target_dir,
        enriched_context=mutated,
    )

    copied = target_dir / "config" / "logging-extra.md"
    assert copied.read_text(encoding="utf-8") == "extra snippet"


def test_missing_snippet_raises(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, base_context: dict[str, object]
) -> None:
    missing = tmp_path / "missing.txt"
    monkeypatch.setenv("RAPIDKIT_LOGGING_EXTRA_SNIPPET", str(missing))
    monkeypatch.setenv("RAPIDKIT_LOGGING_EXTRA_SNIPPET_VARIANTS", "fastapi")

    overrides = LoggingOverrides()
    with pytest.raises(FileNotFoundError):
        overrides.post_variant_generation(
            variant_name="fastapi",
            target_dir=tmp_path,
            enriched_context=base_context,
        )
