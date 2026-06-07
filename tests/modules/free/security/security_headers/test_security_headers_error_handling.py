"""Error handling tests for Security Headers."""

from __future__ import annotations


def test_security_headers_disabled_runtime_is_empty_and_safe(fastapi_adapter) -> None:  # type: ignore[no-untyped-def]
    runtime_module, _ = fastapi_adapter
    runtime = runtime_module.SecurityHeaders(runtime_module.SecurityHeadersConfig(enabled=False))
    target = {"Existing": "value"}

    applied = runtime.apply(target)
    health = runtime.health_check()

    assert applied == {}
    assert target == {"Existing": "value"}
    assert health["status"] == "disabled"
    assert health["metrics"]["header_count"] == 0


def test_security_headers_ignores_empty_policy_values(fastapi_adapter) -> None:  # type: ignore[no-untyped-def]
    runtime_module, _ = fastapi_adapter
    runtime = runtime_module.SecurityHeaders(
        runtime_module.SecurityHeadersConfig(
            permissions_policy={
                "camera": "",
                "geolocation": None,
                "microphone": ["self", ""],
            },
            x_content_type_options=False,
        )
    )

    headers = runtime.headers()

    assert headers["Permissions-Policy"] == "camera=(), geolocation=(), microphone=(self)"
    assert "X-Content-Type-Options" not in headers
