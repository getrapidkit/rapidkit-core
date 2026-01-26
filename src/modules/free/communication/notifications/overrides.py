"""Runtime overrides for the notifications module."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping


class NotificationsOverrides:
    """Runtime customization for notifications generation."""

    def __init__(self, module_root: Path | None = None) -> None:
        self.module_root = module_root
        self.prefix = "RAPIDKIT_NOTIFICATIONS"

    def apply_base_context(self, context: Mapping[str, Any]) -> dict[str, Any]:
        """Apply overrides to base context before variant generation."""
        ctx = dict(context)

        # Optional: Enable advanced email features
        ctx["enable_advanced_email"] = self.get_bool_setting("ENABLE_ADVANCED_EMAIL", default=False)

        # Optional: Configure default email provider
        ctx["default_email_provider"] = self.get_setting("DEFAULT_EMAIL_PROVIDER", default="smtp")

        # Optional: Enable template caching
        ctx["enable_template_caching"] = self.get_bool_setting(
            "ENABLE_TEMPLATE_CACHING", default=True
        )

        return ctx

    def apply_variant_context(self, context: Mapping[str, Any]) -> dict[str, Any]:
        """Apply overrides to variant-specific context."""
        ctx = dict(context)

        # Variant-specific customizations can be added here
        framework = ctx.get("framework", "fastapi")

        if framework == "fastapi":
            ctx["async_email_support"] = True
        elif framework == "nestjs":
            ctx["dependency_injection"] = True

        return ctx

    def get_bool_setting(self, key: str, *, default: bool = False) -> bool:
        """Get a boolean environment setting."""
        value = self.get_setting(key, default=str(default).lower())
        return value.lower() in ("true", "1", "yes", "on")

    def get_setting(self, key: str, *, default: str | None = None) -> str:
        """Get an environment setting with optional default."""
        return os.getenv(f"{self.prefix}_{key}", default or "")
