import json
from pathlib import Path
from typing import Any

import pytest

from modules.free.auth.core.overrides import AuthCoreOverrides

OVERRIDE_ITERATIONS = 123_456
CLAMPED_SALT_BYTES = 8
REQUESTED_SALT_BYTES = 4
TOKEN_BYTES_OVERRIDE = 16
CLAMPED_TTL_SECONDS = 60
REQUESTED_TTL_SECONDS = 30
OVERRIDE_MIN_LENGTH = 16


@pytest.fixture
def base_context() -> dict[str, Any]:
    return {
        "auth_core_defaults": {
            "hash_name": "sha256",
            "iterations": 390_000,
            "salt_bytes": 32,
            "token_bytes": 32,
            "token_ttl_seconds": 1_800,
            "pepper_env": "RAPIDKIT_AUTH_CORE_PEPPER",
            "issuer": "RapidKit",
            "policy": {
                "min_length": 12,
                "require_uppercase": True,
                "require_lowercase": True,
                "require_digits": True,
                "require_symbols": False,
            },
        }
    }


def test_overrides_mutate_defaults(
    monkeypatch: pytest.MonkeyPatch, base_context: dict[str, Any]
) -> None:
    monkeypatch.setenv("RAPIDKIT_AUTH_CORE_HASH", "sha512")
    monkeypatch.setenv("RAPIDKIT_AUTH_CORE_ITERATIONS", str(OVERRIDE_ITERATIONS))
    monkeypatch.setenv("RAPIDKIT_AUTH_CORE_SALT_BYTES", str(REQUESTED_SALT_BYTES))
    monkeypatch.setenv("RAPIDKIT_AUTH_CORE_TOKEN_BYTES", str(TOKEN_BYTES_OVERRIDE))
    monkeypatch.setenv("RAPIDKIT_AUTH_CORE_TOKEN_TTL", str(REQUESTED_TTL_SECONDS))
    monkeypatch.setenv("RAPIDKIT_AUTH_CORE_ISSUER", "ExampleApp")
    monkeypatch.setenv("RAPIDKIT_AUTH_CORE_PEPPER_ENV", "CUSTOM_PEPPER")
    monkeypatch.setenv(
        "RAPIDKIT_AUTH_CORE_POLICY",
        json.dumps({"min_length": OVERRIDE_MIN_LENGTH, "require_symbols": True}),
    )

    overrides = AuthCoreOverrides()
    mutated = overrides.apply_base_context(base_context)

    defaults = mutated["auth_core_defaults"]  # type: ignore[index]
    original = base_context["auth_core_defaults"]

    assert defaults["hash_name"] == "sha512"
    assert defaults["iterations"] == OVERRIDE_ITERATIONS
    assert defaults["salt_bytes"] == CLAMPED_SALT_BYTES
    assert defaults["token_bytes"] == TOKEN_BYTES_OVERRIDE
    assert defaults["token_ttl_seconds"] == CLAMPED_TTL_SECONDS
    assert defaults["issuer"] == "ExampleApp"
    assert defaults["pepper_env"] == "CUSTOM_PEPPER"
    assert defaults["policy"]["min_length"] == OVERRIDE_MIN_LENGTH
    assert defaults["policy"]["require_symbols"] is True

    assert original["hash_name"] == "sha256", "Base context should remain unchanged"


def test_invalid_overrides_are_ignored(
    monkeypatch: pytest.MonkeyPatch, base_context: dict[str, Any]
) -> None:
    base_copy = json.loads(json.dumps(base_context))

    monkeypatch.setenv("RAPIDKIT_AUTH_CORE_ITERATIONS", "not-a-number")
    monkeypatch.setenv("RAPIDKIT_AUTH_CORE_SALT_BYTES", "invalid")
    monkeypatch.setenv("RAPIDKIT_AUTH_CORE_POLICY", "\n not-json ::")

    overrides = AuthCoreOverrides()
    mutated = overrides.apply_variant_context_pre(base_context, variant_name="fastapi")

    defaults = mutated["auth_core_defaults"]  # type: ignore[index]
    assert defaults["iterations"] == base_copy["auth_core_defaults"]["iterations"]
    assert defaults["salt_bytes"] == base_copy["auth_core_defaults"]["salt_bytes"]
    assert defaults["policy"] == base_copy["auth_core_defaults"]["policy"]

    mutated_post = overrides.apply_variant_context_post(base_context, variant_name="fastapi")
    assert mutated_post == mutated

    overrides.post_variant_generation(
        variant_name="fastapi", target_dir=Path("."), enriched_context=mutated
    )
