import json

import pytest

from modules.free.security.rate_limiting.overrides import (
    RateLimitingOverrides,
    RateLimitingOverrideState,
    _merge_rules,
    resolve_override_state,
)


@pytest.fixture(autouse=True)
def clear_rate_limit_env(monkeypatch):
    keys = [
        "RAPIDKIT_RATE_LIMIT_BACKEND",
        "RAPIDKIT_RATE_LIMIT_REDIS_URL",
        "RAPIDKIT_RATE_LIMIT_DEFAULT_LIMIT",
        "RAPIDKIT_RATE_LIMIT_DEFAULT_WINDOW",
        "RAPIDKIT_RATE_LIMIT_DEFAULT_SCOPE",
        "RAPIDKIT_RATE_LIMIT_DEFAULT_PRIORITY",
        "RAPIDKIT_RATE_LIMIT_DEFAULT_BLOCK_SECONDS",
        "RAPIDKIT_RATE_LIMIT_TRUST_FORWARDED_FOR",
        "RAPIDKIT_RATE_LIMIT_FORWARDED_FOR_HEADER",
        "RAPIDKIT_RATE_LIMIT_IDENTITY_HEADER",
        "RAPIDKIT_RATE_LIMIT_EXTRA_RULES",
        "RAPIDKIT_RATE_LIMIT_METADATA",
    ]
    for key in keys:
        monkeypatch.delenv(key, raising=False)


def test_resolve_override_state_reads_env(monkeypatch, tmp_path):
    monkeypatch.setenv("RAPIDKIT_RATE_LIMIT_BACKEND", "redis")
    monkeypatch.setenv("RAPIDKIT_RATE_LIMIT_REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("RAPIDKIT_RATE_LIMIT_DEFAULT_LIMIT", "10")
    monkeypatch.setenv("RAPIDKIT_RATE_LIMIT_DEFAULT_WINDOW", "60")
    monkeypatch.setenv("RAPIDKIT_RATE_LIMIT_DEFAULT_SCOPE", "global")
    monkeypatch.setenv("RAPIDKIT_RATE_LIMIT_DEFAULT_PRIORITY", "5")
    monkeypatch.setenv("RAPIDKIT_RATE_LIMIT_DEFAULT_BLOCK_SECONDS", "120")
    monkeypatch.setenv("RAPIDKIT_RATE_LIMIT_TRUST_FORWARDED_FOR", "yes")
    monkeypatch.setenv("RAPIDKIT_RATE_LIMIT_FORWARDED_FOR_HEADER", "X-Forwarded-For")
    monkeypatch.setenv("RAPIDKIT_RATE_LIMIT_IDENTITY_HEADER", "X-User-Id")
    monkeypatch.setenv(
        "RAPIDKIT_RATE_LIMIT_EXTRA_RULES",
        json.dumps(
            [
                {"name": "burst", "limit": 50, "window": 60},
                {"name": "sustained", "limit": 200, "window": 3600},
            ]
        ),
    )
    monkeypatch.setenv(
        "RAPIDKIT_RATE_LIMIT_METADATA",
        json.dumps({"source": "env", "enabled": True}),
    )

    state = resolve_override_state(tmp_path)

    assert isinstance(state, RateLimitingOverrideState)
    assert state.backend == "redis"
    assert state.redis_url.endswith("6379/0")
    assert state.default_limit == 10
    assert state.default_window == 60
    assert state.default_scope == "global"
    assert state.default_priority == 5
    assert state.default_block_seconds == 120
    assert state.trust_forwarded_for is True
    assert state.forwarded_for_header == "X-Forwarded-For"
    assert state.identity_header == "X-User-Id"
    assert [rule["name"] for rule in state.rules] == ["burst", "sustained"]
    assert state.metadata == {"source": "env", "enabled": True}


def test_resolve_override_state_handles_invalid_values(monkeypatch, tmp_path):
    monkeypatch.setenv("RAPIDKIT_RATE_LIMIT_DEFAULT_LIMIT", "not-an-int")
    monkeypatch.setenv("RAPIDKIT_RATE_LIMIT_TRUST_FORWARDED_FOR", "maybe")
    monkeypatch.setenv("RAPIDKIT_RATE_LIMIT_EXTRA_RULES", "not-json")
    monkeypatch.setenv(
        "RAPIDKIT_RATE_LIMIT_METADATA",
        json.dumps(["not", "a", "mapping"]),
    )

    state = resolve_override_state(tmp_path)

    assert state.default_limit is None
    assert state.trust_forwarded_for is None
    assert state.rules == ()
    assert state.metadata is None


def test_merge_rules_preserves_existing_and_appends_overrides():
    existing_rules = [
        {"name": "existing", "limit": 100, "window": 60},
        {"limit": 50, "window": 30},
    ]
    extra_rules = (
        {"name": "override", "limit": 25},
        {"limit": 10},
    )

    merged = _merge_rules(existing_rules, extra_rules)

    names = {rule.get("name") for rule in merged}
    assert "existing" in names
    assert any(rule.get("name") == "override" for rule in merged)
    assert len(merged) == 4


def test_rate_limiting_overrides_apply_context(monkeypatch, tmp_path):
    monkeypatch.setenv("RAPIDKIT_RATE_LIMIT_BACKEND", "redis")
    monkeypatch.setenv("RAPIDKIT_RATE_LIMIT_DEFAULT_LIMIT", "0")
    monkeypatch.setenv("RAPIDKIT_RATE_LIMIT_DEFAULT_WINDOW", "5")
    monkeypatch.setenv("RAPIDKIT_RATE_LIMIT_DEFAULT_PRIORITY", "-1")
    monkeypatch.setenv("RAPIDKIT_RATE_LIMIT_DEFAULT_BLOCK_SECONDS", "-10")
    monkeypatch.setenv("RAPIDKIT_RATE_LIMIT_TRUST_FORWARDED_FOR", "no")
    monkeypatch.setenv(
        "RAPIDKIT_RATE_LIMIT_EXTRA_RULES",
        json.dumps({"name": "env-rule", "limit": 5}),
    )
    monkeypatch.setenv(
        "RAPIDKIT_RATE_LIMIT_METADATA",
        json.dumps({"override": True}),
    )

    overrides = RateLimitingOverrides(module_root=tmp_path)

    context = {
        "rate_limiting_defaults": {
            "rules": [{"name": "existing", "limit": 1}],
            "metadata": {"existing": True},
        }
    }

    mutated = overrides.apply_base_context(context)
    defaults = mutated["rate_limiting_defaults"]

    assert defaults["backend"] == "redis"
    assert defaults["default_limit"] == 1  # clamped to at least 1
    assert defaults["default_window"] == 5
    assert defaults["default_priority"] == 0  # clamped to non-negative
    assert defaults["default_block_seconds"] == 0
    assert defaults["trust_forwarded_for"] is False
    assert any(rule.get("name") == "env-rule" for rule in defaults["rules"])
    assert defaults["metadata"]["override"] is True
    assert defaults["metadata"]["existing"] is True

    pre_context = overrides.apply_variant_context_pre({}, variant_name="fastapi")
    assert pre_context["framework"] == "fastapi"
    assert pre_context["override_state"] is overrides.state

    post_context = overrides.apply_variant_context_post({"value": 1}, variant_name="fastapi")
    assert post_context == {"value": 1}

    assert (
        overrides.post_variant_generation(
            variant_name="fastapi",
            target_dir=tmp_path,
            enriched_context={},
        )
        is None
    )
