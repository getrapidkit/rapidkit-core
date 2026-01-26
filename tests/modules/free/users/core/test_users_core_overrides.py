"""Unit tests for Users Core overrides."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

_PREFIX = "RAPIDKIT_USERS_CORE"
EXPECTED_MAX_RESULTS = 250
OVERRIDDEN_MAX_RESULTS = 500


def _clear_override_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in list(os.environ):
        if key.startswith(f"{_PREFIX}_"):
            monkeypatch.delenv(key, raising=False)


def test_resolve_override_state_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    from modules.free.users.users_core.overrides import (
        UsersCoreOverrideState,
        resolve_override_state,
    )

    _clear_override_env(monkeypatch)
    monkeypatch.setenv(f"{_PREFIX}_ALLOW_REGISTRATION", "false")
    monkeypatch.setenv(f"{_PREFIX}_ENFORCE_UNIQUE_EMAIL", "true")
    monkeypatch.setenv(f"{_PREFIX}_DEFAULT_LOCALE", "fa-IR")
    monkeypatch.setenv(f"{_PREFIX}_AUDIT_LOG_ENABLED", "0")
    monkeypatch.setenv(f"{_PREFIX}_MAX_RESULTS", str(EXPECTED_MAX_RESULTS))
    monkeypatch.setenv(f"{_PREFIX}_PASSWORDLESS_SUPPORTED", "1")

    state = resolve_override_state(Path("."))

    assert isinstance(state, UsersCoreOverrideState)
    assert state.allow_registration is False
    assert state.enforce_unique_email is True
    assert state.default_locale == "fa-IR"
    assert state.audit_log_enabled is False
    assert state.max_results_per_page == EXPECTED_MAX_RESULTS
    assert state.passwordless_supported is True


def test_apply_base_context_mutates_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    from modules.free.users.users_core.overrides import UsersCoreOverrides

    _clear_override_env(monkeypatch)
    monkeypatch.setenv(f"{_PREFIX}_MAX_RESULTS", str(OVERRIDDEN_MAX_RESULTS))
    monkeypatch.setenv(f"{_PREFIX}_ALLOW_REGISTRATION", "no")

    overrides = UsersCoreOverrides(Path("."))

    base_defaults: dict[str, Any] = {
        "allow_registration": True,
        "max_results_per_page": 100,
        "default_locale": "en",
    }

    context = {"users_core_defaults": base_defaults}

    mutated = overrides.apply_base_context(context)
    mutated_defaults = mutated["users_core_defaults"]

    assert mutated_defaults["allow_registration"] is False
    assert mutated_defaults["max_results_per_page"] == OVERRIDDEN_MAX_RESULTS
    assert mutated_defaults["default_locale"] == "en"


def test_variant_context_methods_delegate(monkeypatch: pytest.MonkeyPatch) -> None:
    from modules.free.users.users_core.overrides import UsersCoreOverrides

    _clear_override_env(monkeypatch)
    overrides = UsersCoreOverrides(Path("."))
    context = {"users_core_defaults": {"allow_registration": True}}

    pre_context = overrides.apply_variant_context_pre(context, variant_name="fastapi")
    post_context = overrides.apply_variant_context_post(context, variant_name="fastapi")

    assert "users_core_defaults" in pre_context
    assert "users_core_defaults" in post_context
    assert pre_context["users_core_defaults"]["allow_registration"] is True
    assert post_context["users_core_defaults"]["allow_registration"] is True


def test_new_env_key_for_max_results(monkeypatch: pytest.MonkeyPatch) -> None:
    """Newer, more descriptive env var name should be respected."""
    from modules.free.users.users_core.overrides import resolve_override_state

    _clear_override_env(monkeypatch)
    monkeypatch.setenv(f"{_PREFIX}_MAX_RESULTS_PER_PAGE", str(EXPECTED_MAX_RESULTS))

    state = resolve_override_state(Path("."))
    assert state.max_results_per_page == EXPECTED_MAX_RESULTS
