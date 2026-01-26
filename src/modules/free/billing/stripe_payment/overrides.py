"""Environment-aware overrides for the Stripe Payment module."""

from __future__ import annotations

import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from core.services.override_contracts import ConfigurableOverrideMixin


@dataclass(frozen=True)
class StripeOverrideState:
    """Snapshot of environment-driven overrides for Stripe payment defaults."""

    api_key: Optional[str] = None
    webhook_secret: Optional[str] = None
    mode: Optional[str] = None
    default_currency: Optional[str] = None
    statement_descriptor: Optional[str] = None
    automatic_payment_methods: Optional[bool] = None
    max_attempts: Optional[int] = None


def _get_env(name: str) -> Optional[str]:
    value = os.getenv(name)
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _parse_bool(name: str) -> Optional[bool]:
    raw = _get_env(name)
    if raw is None:
        return None
    lowered = raw.lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
        return False
    return None


def _parse_int(name: str) -> Optional[int]:
    raw = _get_env(name)
    if raw is None:
        return None
    try:
        parsed = int(raw)
    except ValueError:
        return None
    return max(parsed, 1)


def resolve_override_state(_: Path) -> StripeOverrideState:
    return StripeOverrideState(
        api_key=_get_env("RAPIDKIT_STRIPE_API_KEY"),
        webhook_secret=_get_env("RAPIDKIT_STRIPE_WEBHOOK_SECRET"),
        mode=_get_env("RAPIDKIT_STRIPE_MODE"),
        default_currency=_get_env("RAPIDKIT_STRIPE_DEFAULT_CURRENCY"),
        statement_descriptor=_get_env("RAPIDKIT_STRIPE_STATEMENT_DESCRIPTOR"),
        automatic_payment_methods=_parse_bool("RAPIDKIT_STRIPE_AUTOMATIC_PAYMENT_METHODS"),
        max_attempts=_parse_int("RAPIDKIT_STRIPE_MAX_RETRIES"),
    )


class StripePaymentOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Stripe Payment."""

    def __init__(self, module_root: Path | None = None) -> None:
        self.module_root = module_root or Path(__file__).resolve().parent
        super().__init__()

    def apply_base_context(self, context: Mapping[str, Any]) -> dict[str, Any]:
        state = resolve_override_state(self.module_root)
        mutated = dict(context)

        defaults = dict(mutated.get("stripe_defaults", {}))
        if state.mode:
            defaults["mode"] = state.mode.lower()
        if state.default_currency:
            defaults["default_currency"] = state.default_currency.lower()
        if state.statement_descriptor:
            defaults["statement_descriptor"] = state.statement_descriptor
        if state.automatic_payment_methods is not None:
            defaults["automatic_payment_methods"] = state.automatic_payment_methods
        mutated["stripe_defaults"] = defaults

        retry_policy = dict(mutated.get("stripe_retry_policy", {}))
        if state.max_attempts is not None:
            retry_policy["max_attempts"] = state.max_attempts
        mutated["stripe_retry_policy"] = retry_policy

        env_payload = {
            "api_key": state.api_key,
            "webhook_secret": state.webhook_secret,
        }
        mutated["stripe_env_overrides"] = env_payload
        return mutated

    def apply_variant_context_pre(
        self,
        context: Mapping[str, Any],
        *,
        variant_name: str,
    ) -> dict[str, Any]:  # noqa: ARG002
        return self.apply_base_context(context)

    def apply_variant_context_post(
        self,
        context: Mapping[str, Any],
        *,
        variant_name: str,
    ) -> dict[str, Any]:  # noqa: ARG002
        return self.apply_base_context(context)

    def post_variant_generation(
        self,
        *,
        variant_name: str,
        target_dir: Path,
        enriched_context: Mapping[str, Any],
    ) -> None:  # noqa: ARG002
        if variant_name == "fastapi":
            self._ensure_packages(target_dir)
            self._extend_src_namespace(target_dir)

    @staticmethod
    def _ensure_packages(target_dir: Path) -> None:
        src_root = target_dir / "src"
        package_paths = [
            src_root,
            src_root / "billing",
            src_root / "health",
            src_root / "routers",
            src_root / "types",
        ]
        for pkg in package_paths:
            pkg.mkdir(parents=True, exist_ok=True)
            init_file = pkg / "__init__.py"
            if not init_file.exists():
                init_file.write_text(
                    '"""Generated package scaffold for Stripe Payment module."""\n',
                    encoding="utf-8",
                )

    @staticmethod
    def _extend_src_namespace(target_dir: Path) -> None:
        package_root = target_dir / "src"
        if not package_root.exists():
            return

        src_module = sys.modules.get("src")
        if src_module is None:
            return

        package_path = str(package_root.resolve())
        module_path = getattr(src_module, "__path__", None)
        if module_path is None:
            return

        try:
            paths = list(module_path)
        except TypeError:
            return

        if package_path in paths:
            return

        append_path: Callable[[str], Any] | None = getattr(module_path, "append", None)
        if append_path is not None:
            append_path(package_path)
            return

        src_module.__path__ = paths + [package_path]


__all__ = [
    "StripePaymentOverrides",
    "StripeOverrideState",
    "resolve_override_state",
]
