"""Validation tests for Api Keys."""

from __future__ import annotations


def test_api_keys_scope_allowlist_blocks_unknown_scope(rendered_api_keys) -> None:  # type: ignore[no-untyped-def]
    runtime_mod = rendered_api_keys["runtime"]
    runtime = runtime_mod.ApiKeys(
        {
            "pepper": "test-pepper",
            "allowed_scopes": ("read",),
        }
    )

    try:
        runtime.issue_key("owner-1", scopes=["write"])
    except runtime_mod.ApiKeysConfigurationError as exc:
        assert "not permitted" in str(exc)
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("Expected scope allowlist validation to fail")


def test_api_keys_wildcard_scopes_can_grant_required_scope(rendered_api_keys) -> None:  # type: ignore[no-untyped-def]
    runtime_mod = rendered_api_keys["runtime"]
    runtime = runtime_mod.ApiKeys(
        {
            "pepper": "test-pepper",
            "allowed_scopes": ("admin:*",),
            "allow_scope_wildcards": True,
        }
    )

    issued = runtime.issue_key("owner-1", scopes=["admin:*"])
    verification = runtime.verify_token(issued.token, required_scopes=["admin:read"])

    assert verification.matched is True
    assert verification.scopes_granted == ("admin:read",)
