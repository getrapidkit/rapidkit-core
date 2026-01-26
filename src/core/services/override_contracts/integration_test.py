# src/core/services/override_contracts/integration_test.py
"""Integration test for override contracts with modules."""

from __future__ import annotations

from typing import Any, Dict, Type, cast

from . import apply_module_overrides

DEFAULT_TIMEOUT_SECONDS = 30


class TestService:
    """Test service for override integration."""

    def __init__(self) -> None:
        self.timeout = DEFAULT_TIMEOUT_SECONDS

    def make_request(self, url: str) -> Dict[str, Any]:
        """Make a request."""
        return {"url": url, "timeout": self.timeout, "method": "GET"}


def test_module_override_integration() -> None:
    """Test that module overrides work with the integration system."""
    # Apply settings module overrides to TestService
    EnhancedService = cast(Type[TestService], apply_module_overrides(TestService, "settings"))

    # Create instance
    service = EnhancedService()

    # Test that basic functionality works
    result = service.make_request("https://api.example.com")
    if result["url"] != "https://api.example.com":
        raise RuntimeError("Unexpected URL returned from override test")
    if result["timeout"] != DEFAULT_TIMEOUT_SECONDS:
        raise RuntimeError("Unexpected timeout returned from override test")
    if result["method"] != "GET":
        raise RuntimeError("Unexpected method returned from override test")

    print("✅ Module override integration test passed!")


if __name__ == "__main__":
    test_module_override_integration()
