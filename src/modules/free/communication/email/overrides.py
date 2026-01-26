"""Override contracts for the RapidKit Email module."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

from core.services.override_contracts import ConfigurableOverrideMixin

from .frameworks.nestjs import NestJSPlugin


@dataclass(frozen=True)
class EmailOverrideState:
    """Snapshot of environment-driven overrides for default email configuration."""

    enabled: Optional[bool] = None
    provider: Optional[str] = None
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    reply_to: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: Optional[bool] = None
    template_directory: Optional[str] = None
    dry_run: Optional[bool] = None
    default_headers: Mapping[str, str] = field(default_factory=dict)


TRUTHY = {"1", "true", "yes", "on"}
FALSY = {"0", "false", "no", "off"}


def _get_env(name: str) -> Optional[str]:
    value = os.getenv(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _parse_bool(name: str) -> Optional[bool]:
    raw = _get_env(name)
    if raw is None:
        return None
    lowered = raw.lower()
    if lowered in TRUTHY:
        return True
    if lowered in FALSY:
        return False
    return None


def _parse_int(name: str) -> Optional[int]:
    raw = _get_env(name)
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _parse_headers(name: str) -> Mapping[str, str]:
    raw = _get_env(name)
    if not raw:
        return {}
    headers: dict[str, str] = {}
    for entry in raw.split(","):
        if "=" not in entry:
            continue
        key, value = entry.split("=", 1)
        headers[key.strip()] = value.strip()
    return headers


def resolve_override_state() -> EmailOverrideState:
    return EmailOverrideState(
        enabled=_parse_bool("RAPIDKIT_EMAIL_ENABLED"),
        provider=_get_env("RAPIDKIT_EMAIL_PROVIDER"),
        from_email=_get_env("RAPIDKIT_EMAIL_FROM_ADDRESS"),
        from_name=_get_env("RAPIDKIT_EMAIL_FROM_NAME"),
        reply_to=_get_env("RAPIDKIT_EMAIL_REPLY_TO"),
        smtp_host=_get_env("RAPIDKIT_EMAIL_SMTP_HOST"),
        smtp_port=_parse_int("RAPIDKIT_EMAIL_SMTP_PORT"),
        smtp_username=_get_env("RAPIDKIT_EMAIL_SMTP_USERNAME"),
        smtp_password=_get_env("RAPIDKIT_EMAIL_SMTP_PASSWORD"),
        smtp_use_tls=_parse_bool("RAPIDKIT_EMAIL_SMTP_USE_TLS"),
        template_directory=_get_env("RAPIDKIT_EMAIL_TEMPLATE_DIRECTORY"),
        dry_run=_parse_bool("RAPIDKIT_EMAIL_DRY_RUN"),
        default_headers=_parse_headers("RAPIDKIT_EMAIL_DEFAULT_HEADERS"),
    )


def _ensure_dict(container: dict[str, Any], key: str) -> dict[str, Any]:
    value = container.get(key)
    if not isinstance(value, dict):
        value = {}
        container[key] = value
    return value


class EmailOverrides(ConfigurableOverrideMixin):
    """Extend or customise generator behaviour for the Email module."""

    def __init__(self, module_root: Path | None = None) -> None:
        self.module_root = module_root or Path(__file__).resolve().parent
        self.state = resolve_override_state()
        super().__init__()

    def apply_base_context(self, context: Mapping[str, Any]) -> dict[str, Any]:
        mutated = dict(context)
        defaults = dict(mutated.get("email_defaults", {}))
        state = self.state

        if state.enabled is not None:
            defaults["enabled"] = state.enabled
        if state.provider:
            defaults["provider"] = state.provider
        if state.from_email:
            defaults["from_email"] = state.from_email
        if state.from_name:
            defaults["from_name"] = state.from_name
        if state.reply_to:
            defaults["reply_to"] = state.reply_to
        if state.smtp_host:
            smtp_defaults = _ensure_dict(defaults, "smtp")
            smtp_defaults["host"] = state.smtp_host
        if state.smtp_port is not None:
            smtp_defaults = _ensure_dict(defaults, "smtp")
            smtp_defaults["port"] = max(state.smtp_port, 1)
        if state.smtp_username is not None:
            smtp_defaults = _ensure_dict(defaults, "smtp")
            smtp_defaults["username"] = state.smtp_username
        if state.smtp_password is not None:
            smtp_defaults = _ensure_dict(defaults, "smtp")
            smtp_defaults["password"] = state.smtp_password
        if state.smtp_use_tls is not None:
            smtp_defaults = _ensure_dict(defaults, "smtp")
            smtp_defaults["use_tls"] = state.smtp_use_tls
        if state.template_directory:
            template_defaults = _ensure_dict(defaults, "template")
            template_defaults["directory"] = state.template_directory
        if state.dry_run is not None:
            defaults["dry_run"] = state.dry_run
        if state.default_headers:
            headers = dict(defaults.get("default_headers", {}))
            headers.update(state.default_headers)
            defaults["default_headers"] = headers

        mutated["email_defaults"] = defaults
        metadata = dict(mutated.get("override_metadata", {}))
        metadata["email_env_overrides"] = True
        mutated["override_metadata"] = metadata
        return mutated

    def apply_variant_context_pre(
        self,
        context: Mapping[str, Any],
        *,
        variant_name: str,
    ) -> dict[str, Any]:
        mutated = dict(context)
        mutated.setdefault("override_state", self.state)
        mutated.setdefault("framework", variant_name)
        return mutated

    def apply_variant_context_post(
        self,
        context: Mapping[str, Any],
        *,
        variant_name: str,
    ) -> dict[str, Any]:  # noqa: ARG002
        return dict(context)

    def post_variant_generation(
        self,
        *,
        variant_name: str,
        target_dir: Path,
        enriched_context: Mapping[str, Any],
    ) -> None:  # noqa: D401, ARG002
        """Apply post-generation adjustments for specific variants."""

        if variant_name.startswith("nestjs"):
            package_path = target_dir / "package.json"
            if package_path.exists():
                plugin = NestJSPlugin()
                ensure_deps = getattr(plugin, "_ensure_package_dependencies", None)
                if callable(ensure_deps):
                    ensure_deps(package_path)
