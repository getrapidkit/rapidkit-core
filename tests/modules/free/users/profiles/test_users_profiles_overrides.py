"""Unit tests for Users Profiles overrides."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

_PREFIX = "RAPIDKIT_USERS_PROFILES"
DEFAULT_SOCIAL_LIMIT = 5
OVERRIDDEN_SOCIAL_LIMIT = 7
EXPECTED_MAX_BIO_LENGTH = 600
EXPECTED_AVATAR_MAX_BYTES = 5_242_880
EXPECTED_SOCIAL_LINKS_LIMIT = 3


def _clear_override_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in list(os.environ):
        if key.startswith(f"{_PREFIX}_"):
            monkeypatch.delenv(key, raising=False)


def test_resolve_override_state_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    from modules.free.users.users_profiles.overrides import (
        UsersProfileOverrideState,
        resolve_override_state,
    )

    _clear_override_env(monkeypatch)
    monkeypatch.setenv(f"{_PREFIX}_DEFAULT_TIMEZONE", "Europe/Paris")
    monkeypatch.setenv(f"{_PREFIX}_MAX_BIO_LENGTH", str(EXPECTED_MAX_BIO_LENGTH))
    monkeypatch.setenv(f"{_PREFIX}_AVATAR_MAX_BYTES", str(EXPECTED_AVATAR_MAX_BYTES))
    monkeypatch.setenv(f"{_PREFIX}_ALLOW_MARKETING_OPT_IN", "false")
    monkeypatch.setenv(f"{_PREFIX}_SOCIAL_LINKS_LIMIT", str(EXPECTED_SOCIAL_LINKS_LIMIT))
    monkeypatch.setenv(f"{_PREFIX}_DEFAULT_VISIBILITY", "private")

    state = resolve_override_state(Path("."))

    assert isinstance(state, UsersProfileOverrideState)
    assert state.default_timezone == "Europe/Paris"
    assert state.max_bio_length == EXPECTED_MAX_BIO_LENGTH
    assert state.avatar_max_bytes == EXPECTED_AVATAR_MAX_BYTES
    assert state.allow_marketing_opt_in is False
    assert state.social_links_limit == EXPECTED_SOCIAL_LINKS_LIMIT
    assert state.default_visibility == "private"


def test_apply_base_context_mutates_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    from modules.free.users.users_profiles.overrides import UsersProfileOverrides

    _clear_override_env(monkeypatch)
    monkeypatch.setenv(f"{_PREFIX}_SOCIAL_LINKS_LIMIT", str(OVERRIDDEN_SOCIAL_LIMIT))

    overrides = UsersProfileOverrides(Path("."))

    base_defaults: dict[str, Any] = {
        "social_links_limit": DEFAULT_SOCIAL_LIMIT,
        "default_timezone": "UTC",
    }

    context = {"users_profiles_defaults": base_defaults}

    mutated = overrides.apply_base_context(context)
    mutated_defaults = mutated["users_profiles_defaults"]

    assert mutated_defaults["social_links_limit"] == OVERRIDDEN_SOCIAL_LIMIT
    assert mutated_defaults["default_timezone"] == "UTC"


def test_variant_context_methods_delegate(monkeypatch: pytest.MonkeyPatch) -> None:
    from modules.free.users.users_profiles.overrides import UsersProfileOverrides

    _clear_override_env(monkeypatch)
    overrides = UsersProfileOverrides(Path("."))
    context = {"users_profiles_defaults": {"default_visibility": "public"}}

    pre_context = overrides.apply_variant_context_pre(context, variant_name="fastapi")
    post_context = overrides.apply_variant_context_post(context, variant_name="fastapi")

    assert "users_profiles_defaults" in pre_context
    assert "users_profiles_defaults" in post_context
    assert pre_context["users_profiles_defaults"]["default_visibility"] == "public"
    assert post_context["users_profiles_defaults"]["default_visibility"] == "public"
