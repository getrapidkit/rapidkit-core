"""Error handling tests for Api Keys."""

from __future__ import annotations


def test_api_keys_requires_configured_pepper(rendered_api_keys) -> None:  # type: ignore[no-untyped-def]
    runtime_mod = rendered_api_keys["runtime"]
    runtime = runtime_mod.ApiKeys()

    try:
        runtime.issue_key("owner-1")
    except runtime_mod.ApiKeysConfigurationError as exc:
        assert "Pepper must be configured" in str(exc)
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("Expected missing pepper to fail issuance")


def test_api_keys_rejects_malformed_tokens(rendered_api_keys) -> None:  # type: ignore[no-untyped-def]
    runtime_mod = rendered_api_keys["runtime"]
    runtime = runtime_mod.ApiKeys({"pepper": "test-pepper"})

    try:
        runtime.verify_token("not-a-token")
    except runtime_mod.ApiKeysVerificationError as exc:
        assert "Token format invalid" in str(exc)
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("Expected malformed token to fail verification")


def test_api_keys_rejects_unknown_revocation_target(rendered_api_keys) -> None:  # type: ignore[no-untyped-def]
    runtime_mod = rendered_api_keys["runtime"]
    runtime = runtime_mod.ApiKeys({"pepper": "test-pepper"})

    try:
        runtime.revoke_key("missing")
    except runtime_mod.ApiKeysRepositoryError as exc:
        assert "does not exist" in str(exc)
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("Expected missing key revocation to fail")
