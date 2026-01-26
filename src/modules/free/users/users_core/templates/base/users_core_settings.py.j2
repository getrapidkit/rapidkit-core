"""Service settings helper for Users Core."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import MutableMapping


@dataclass
class UsersServiceSettings:
    """Simple structured settings for Users service."""

    allow_registration: bool = True
    enforce_unique_email: bool = True
    default_locale: str = "en"
    audit_log_enabled: bool = True
    max_results_per_page: int = 100
    passwordless_supported: bool = False
    supported_locales: tuple[str, ...] = field(default_factory=lambda: ("en",))

    def validate(self) -> None:
        if self.max_results_per_page <= 0:
            raise ValueError("max_results_per_page must be positive")

    def as_mapping(self) -> MutableMapping[str, object]:
        return {
            "allow_registration": self.allow_registration,
            "enforce_unique_email": self.enforce_unique_email,
            "default_locale": self.default_locale,
            "audit_log_enabled": self.audit_log_enabled,
            "max_results_per_page": self.max_results_per_page,
            "passwordless_supported": self.passwordless_supported,
            "supported_locales": list(self.supported_locales),
        }


__all__ = ["UsersServiceSettings"]
