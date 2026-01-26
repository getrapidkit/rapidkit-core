from pathlib import Path

import pytest

from modules.free.cache.redis.overrides import RedisOverrides

FORCED_PORT = 6380
FORCED_DB = 2
FORCED_RETRIES = 5
FORCED_BACKOFF = 1.5
FORCED_TTL = 7200


@pytest.fixture
def base_context() -> dict[str, object]:
    return {
        "redis_defaults": {
            "url": "redis://localhost:6379/0",
            "host": "localhost",
            "port": 6379,
            "db": 0,
            "password": "",
            "use_tls": False,
            "preconnect": False,
            "connect_retries": 3,
            "connect_backoff_base": 0.5,
            "cache_ttl": 3600,
        },
        "project_name": "RapidKit App",
        "project_slug": "rapidkit-app",
    }


def test_overrides_mutate_defaults_and_copy_snippet(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, base_context: dict[str, object]
) -> None:
    snippet = tmp_path / "redis-extra.md"
    snippet.write_text("extra snippet", encoding="utf-8")

    monkeypatch.setenv("RAPIDKIT_REDIS_FORCE_URL", "redis://cache.internal:6380/2")
    monkeypatch.setenv("RAPIDKIT_REDIS_FORCE_HOST", "cache.internal")
    monkeypatch.setenv("RAPIDKIT_REDIS_FORCE_PORT", str(FORCED_PORT))
    monkeypatch.setenv("RAPIDKIT_REDIS_FORCE_DB", str(FORCED_DB))
    monkeypatch.setenv("RAPIDKIT_REDIS_FORCE_PASSWORD", "secret")
    monkeypatch.setenv("RAPIDKIT_REDIS_FORCE_TLS", "true")
    monkeypatch.setenv("RAPIDKIT_REDIS_FORCE_PRECONNECT", "yes")
    monkeypatch.setenv("RAPIDKIT_REDIS_FORCE_RETRIES", str(FORCED_RETRIES))
    monkeypatch.setenv("RAPIDKIT_REDIS_FORCE_BACKOFF", str(FORCED_BACKOFF))
    monkeypatch.setenv("RAPIDKIT_REDIS_FORCE_TTL", str(FORCED_TTL))
    monkeypatch.setenv("RAPIDKIT_REDIS_PROJECT_NAME", "Cache Service")
    monkeypatch.setenv("RAPIDKIT_REDIS_EXTRA_SNIPPET", str(snippet))
    monkeypatch.setenv("RAPIDKIT_REDIS_EXTRA_SNIPPET_DEST", "config/redis-extra.md")
    monkeypatch.setenv("RAPIDKIT_REDIS_EXTRA_SNIPPET_VARIANTS", '["fastapi"]')

    overrides = RedisOverrides()
    mutated = overrides.apply_base_context(base_context)

    defaults = mutated["redis_defaults"]  # type: ignore[index]
    assert defaults["url"] == "redis://cache.internal:6380/2"
    assert defaults["host"] == "cache.internal"
    assert defaults["port"] == FORCED_PORT
    assert defaults["db"] == FORCED_DB
    assert defaults["password"] == "secret"
    assert defaults["use_tls"] is True
    assert defaults["preconnect"] is True
    assert defaults["connect_retries"] == FORCED_RETRIES
    assert defaults["connect_backoff_base"] == FORCED_BACKOFF
    assert defaults["cache_ttl"] == FORCED_TTL
    assert mutated["project_name"] == "Cache Service"
    assert mutated["project_slug"] == "cache-service"

    target_dir = tmp_path / "project"
    target_dir.mkdir()
    overrides.post_variant_generation(
        variant_name="fastapi",
        target_dir=target_dir,
        enriched_context=mutated,
    )

    copied = target_dir / "config" / "redis-extra.md"
    assert copied.read_text(encoding="utf-8") == "extra snippet"


def test_missing_snippet_raises(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, base_context: dict[str, object]
) -> None:
    missing = tmp_path / "missing.md"
    monkeypatch.setenv("RAPIDKIT_REDIS_EXTRA_SNIPPET", str(missing))
    monkeypatch.setenv("RAPIDKIT_REDIS_EXTRA_SNIPPET_VARIANTS", '["fastapi"]')

    overrides = RedisOverrides()
    with pytest.raises(FileNotFoundError):
        overrides.post_variant_generation(
            variant_name="fastapi",
            target_dir=tmp_path,
            enriched_context=base_context,
        )
