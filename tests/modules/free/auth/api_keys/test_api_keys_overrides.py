"""Override scaffolding tests for Api Keys."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch

from modules.free.auth.api_keys import overrides

ROTATION_DAYS = 7
TTL_HOURS = 48
MAX_ACTIVE = 6
LEAK_WINDOW = 12


def test_override_class_declared(module_root: Path) -> None:
    overrides_source = (module_root / "overrides.py").read_text(encoding="utf-8")
    assert "class ApiKeysOverrides" in overrides_source


def test_resolve_override_state_reads_environment(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    snippet_path = tmp_path / "snippet.txt"
    snippet_path.write_text("console.log('api keys');", encoding="utf-8")

    monkeypatch.setenv("RAPIDKIT_API_KEYS_DEFAULT_SCOPES", json.dumps(["read", "write", "read"]))
    monkeypatch.setenv("RAPIDKIT_API_KEYS_ALLOWED_SCOPES", "admin, user, admin")
    monkeypatch.setenv("RAPIDKIT_API_KEYS_ROTATION_DAYS", str(ROTATION_DAYS))
    monkeypatch.setenv("RAPIDKIT_API_KEYS_TTL_HOURS", str(TTL_HOURS))
    monkeypatch.setenv("RAPIDKIT_API_KEYS_MAX_ACTIVE", str(MAX_ACTIVE))
    monkeypatch.setenv("RAPIDKIT_API_KEYS_LEAK_WINDOW", str(LEAK_WINDOW))
    monkeypatch.setenv("RAPIDKIT_API_KEYS_PERSIST_LAST_USED", "true")
    monkeypatch.setenv("RAPIDKIT_API_KEYS_AUDIT_TRAIL", "0")
    monkeypatch.setenv("RAPIDKIT_API_KEYS_REPOSITORY", "redis")
    monkeypatch.setenv("RAPIDKIT_API_KEYS_FEATURES", json.dumps(["rotate", "rotate", "audit"]))
    monkeypatch.setenv("RAPIDKIT_API_KEYS_PEPPER_ENV", "RAPIDKIT_PEPPER")
    monkeypatch.setenv("RAPIDKIT_API_KEYS_EXTRA_SNIPPET", str(snippet_path))
    monkeypatch.setenv("RAPIDKIT_API_KEYS_EXTRA_SNIPPET_DEST", "extras/snippet.ts")
    monkeypatch.setenv("RAPIDKIT_API_KEYS_EXTRA_SNIPPET_VARIANTS", "fastapi,nestjs")

    state = overrides.resolve_override_state(Path("."))

    assert state.default_scopes == ("read", "write")
    assert state.allowed_scopes == ("admin", "user")
    assert state.rotation_days == ROTATION_DAYS
    assert state.ttl_hours == TTL_HOURS
    assert state.max_active_per_owner == MAX_ACTIVE
    assert state.leak_window_hours == LEAK_WINDOW
    assert state.persist_last_used is True
    assert state.audit_trail is False
    assert state.repository_backend == "redis"
    assert state.features == ("rotate", "audit")
    assert state.pepper_env == "RAPIDKIT_PEPPER"
    assert state.extra_snippet_source == snippet_path
    assert state.extra_snippet_destination == Path("extras/snippet.ts")
    assert state.extra_snippet_variants == ("fastapi", "nestjs")


def test_apply_base_context_merges_defaults(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    snippet_path = tmp_path / "override.json"
    snippet_path.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("RAPIDKIT_API_KEYS_EXTRA_SNIPPET", str(snippet_path))

    overrides_instance = overrides.ApiKeysOverrides(module_root=Path("."))
    context = {"api_keys_defaults": {"rotation_days": 1, "ttl_hours": 2}}
    merged = overrides_instance.apply_base_context(context)

    assert merged is not context
    assert merged[overrides.DEFAULTS_KEY]["rotation_days"] >= 0
    assert merged[overrides.DEFAULTS_KEY]["ttl_hours"] >= 0


def test_post_variant_generation_copies_snippet(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    module_root = tmp_path / "module"
    module_root.mkdir()
    snippet_source = module_root / "snippet.ts"
    snippet_source.write_text("export const extra = true;", encoding="utf-8")

    monkeypatch.setenv("RAPIDKIT_API_KEYS_EXTRA_SNIPPET", "snippet.ts")
    monkeypatch.setenv("RAPIDKIT_API_KEYS_EXTRA_SNIPPET_DEST", "extras/extra.ts")
    monkeypatch.setenv("RAPIDKIT_API_KEYS_EXTRA_SNIPPET_VARIANTS", json.dumps(["fastapi"]))

    overrides_instance = overrides.ApiKeysOverrides(module_root=module_root)
    target_dir = tmp_path / "generated"

    overrides_instance.post_variant_generation(
        variant_name="nestjs",  # filtered by variants list
        target_dir=target_dir,
        enriched_context={},
    )
    assert not (target_dir / "extras" / "extra.ts").exists()

    overrides_instance.post_variant_generation(
        variant_name="fastapi",
        target_dir=target_dir,
        enriched_context={},
    )
    copied = target_dir / "extras" / "extra.ts"
    assert copied.exists()
    assert copied.read_text(encoding="utf-8").strip()


def test_post_variant_generation_missing_source(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    module_root = tmp_path
    monkeypatch.setenv("RAPIDKIT_API_KEYS_EXTRA_SNIPPET", "missing.txt")

    overrides_instance = overrides.ApiKeysOverrides(module_root=module_root)
    with pytest.raises(FileNotFoundError):
        overrides_instance.post_variant_generation(
            variant_name="fastapi",
            target_dir=tmp_path,
            enriched_context={},
        )
