"""Runtime behaviour tests for Api Keys."""

from __future__ import annotations


def test_api_keys_issue_verify_and_touch_last_used(rendered_api_keys) -> None:  # type: ignore[no-untyped-def]
    runtime_mod = rendered_api_keys["runtime"]
    runtime = runtime_mod.ApiKeys(
        {
            "pepper": "test-pepper",
            "allowed_scopes": ("read", "write"),
            "ttl_hours": 1,
            "max_active_per_owner": 2,
        }
    )

    issued = runtime.issue_key("owner-1", scopes=["read"], label="ci")
    verification = runtime.verify_token(issued.token, required_scopes=["read"])

    assert issued.token.startswith(issued.record.prefix)
    assert issued.secret not in issued.record.hashed_key
    assert verification.matched is True
    assert verification.record is not None
    assert verification.record.last_used_at is not None
    assert runtime.list_keys("owner-1") == [verification.record]


def test_api_keys_rejects_bad_secret_and_scope_mismatch(rendered_api_keys) -> None:  # type: ignore[no-untyped-def]
    runtime_mod = rendered_api_keys["runtime"]
    runtime = runtime_mod.ApiKeys(
        {
            "pepper": "test-pepper",
            "allowed_scopes": ("read", "write"),
        }
    )
    issued = runtime.issue_key("owner-1", scopes=["read"])

    wrong_secret = f"{issued.record.prefix}.wrong"
    wrong = runtime.verify_token(wrong_secret, required_scopes=["read"])
    missing_scope = runtime.verify_token(issued.token, required_scopes=["write"])

    assert wrong.matched is False
    assert wrong.reason == "credentials_mismatch"
    assert missing_scope.matched is False
    assert missing_scope.reason == "scope_mismatch"
    assert runtime.health_check()["telemetry"]["failures"]["credentials_mismatch"] == 1


def test_api_keys_enforces_owner_active_limit(rendered_api_keys) -> None:  # type: ignore[no-untyped-def]
    runtime_mod = rendered_api_keys["runtime"]
    runtime = runtime_mod.ApiKeys({"pepper": "test-pepper", "max_active_per_owner": 1})

    runtime.issue_key("owner-1")

    try:
        runtime.issue_key("owner-1")
    except runtime_mod.ApiKeysRateLimitError as exc:
        assert "active key limit" in str(exc)
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("Expected active key limit to be enforced")


def test_api_keys_revocation_marks_key_inactive(rendered_api_keys) -> None:  # type: ignore[no-untyped-def]
    runtime_mod = rendered_api_keys["runtime"]
    runtime = runtime_mod.ApiKeys({"pepper": "test-pepper"})
    issued = runtime.issue_key("owner-1", scopes=["read"])

    revoked = runtime.revoke_key(issued.record.key_id, reason="rotation")
    verification = runtime.verify_token(issued.token, required_scopes=["read"])

    assert revoked.revoked_at is not None
    assert verification.matched is False
    assert verification.reason == runtime_mod.ApiKeysStatus.REVOKED.value
    assert runtime.list_keys("owner-1") == []
    assert runtime.list_keys("owner-1", include_inactive=True)[0].metadata[
        "revocation_reasons"
    ] == ["rotation"]
