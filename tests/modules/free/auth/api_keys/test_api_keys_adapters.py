"""Adapter integration tests for Api Keys."""

from __future__ import annotations


def test_api_keys_factory_returns_cached_runtime(rendered_api_keys) -> None:  # type: ignore[no-untyped-def]
    runtime_mod = rendered_api_keys["runtime"]
    runtime_mod.reset_runtime_cache()

    first = runtime_mod.get_api_keys_runtime({"pepper": "test-pepper"})
    second = runtime_mod.get_api_keys_runtime({"pepper": "test-pepper"})
    runtime_mod.reset_runtime_cache()
    cached_one = runtime_mod.get_api_keys_runtime()
    cached_two = runtime_mod.get_api_keys_runtime()

    assert first is not second
    assert cached_one is cached_two


def test_api_keys_audit_sink_receives_events(rendered_api_keys) -> None:  # type: ignore[no-untyped-def]
    runtime_mod = rendered_api_keys["runtime"]
    events = []

    class Sink:
        def write(self, entry) -> None:  # type: ignore[no-untyped-def]
            events.append(entry)

    runtime = runtime_mod.ApiKeys({"pepper": "test-pepper"}, audit_sink=Sink())
    issued = runtime.issue_key("owner-1")
    runtime.verify_token(issued.token)

    assert [event.event for event in events] == ["issue", "verify"]
