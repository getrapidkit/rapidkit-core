"""Override scaffolding tests for Db Mongo."""

from __future__ import annotations

from pathlib import Path

from modules.free.database.db_mongo.overrides import DbMongoOverrides


def test_override_class_declared(module_root: Path) -> None:
    overrides_source = (module_root / "overrides.py").read_text(encoding="utf-8")
    assert "class DbMongoOverrides" in overrides_source


def test_environment_overrides_mutate_context(monkeypatch) -> None:
    monkeypatch.setenv("RAPIDKIT_DB_MONGO_URI", "mongodb://example.test:27017")
    monkeypatch.setenv("RAPIDKIT_DB_MONGO_MAX_POOL_SIZE", "42")
    monkeypatch.setenv("RAPIDKIT_DB_MONGO_HEALTH_TIMEOUT_MS", "2500")

    overrides = DbMongoOverrides()
    context = {
        "default_connection_uri": "mongodb://localhost:27017",
        "default_pool_max_size": 20,
        "default_health_timeout_ms": 1500,
        "mongo_defaults": {
            "connection_uri": "mongodb://localhost:27017",
            "max_pool_size": 20,
        },
        "health_defaults": {"ping_timeout_ms": 1500},
    }

    mutated = overrides.apply_base_context(context)

    assert mutated["default_connection_uri"] == "mongodb://example.test:27017"
    assert mutated["default_pool_max_size"] == 42
    assert mutated["default_health_timeout_ms"] == 2500
    assert mutated["mongo_defaults"]["connection_uri"] == "mongodb://example.test:27017"
