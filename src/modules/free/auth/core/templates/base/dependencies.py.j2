"""Dependency helpers exposing Auth Core runtime to FastAPI."""

from __future__ import annotations

from functools import lru_cache
from importlib import import_module
from typing import Any, Dict

from src.modules.free.auth.core.auth.core import AuthCoreRuntime, AuthCoreSettings, load_settings

try:  # pragma: no cover - dependency injection is optional at generation time
    from fastapi import Depends
except ImportError:  # pragma: no cover - FastAPI not installed for linting
    class Depends:  # type: ignore[override]
        def __init__(self, dependency: object | None = None) -> None:
            self.dependency = dependency


def _resolve_settings_module() -> Any:
    candidates = (
        "src.modules.free.essentials.settings.settings",
        "src.settings",
    )
    for candidate in candidates:
        try:
            return import_module(candidate)
        except ModuleNotFoundError:
            continue
        except ImportError:
            continue
    return None


def _get_project_settings_instance() -> Any:
    module = _resolve_settings_module()
    if module is None:
        return None

    provider = getattr(module, "get_settings", None)
    if callable(provider):
        try:
            return provider()
        except Exception:  # pragma: no cover - defensive in case project settings fail
            return None

    settings_cls = getattr(module, "Settings", None)
    if settings_cls is None:
        return None

    try:
        return settings_cls()
    except Exception:  # pragma: no cover - defensive instantiation guard
        return None


def _settings_overrides() -> Dict[str, Any]:
    settings_instance = _get_project_settings_instance()
    if settings_instance is None:
        return {}

    overrides: Dict[str, Any] = {}

    attr_map = (
        ("AUTH_HASH_NAME", "hash_name"),
        ("AUTH_HASH_ITERATIONS", "iterations"),
        ("AUTH_SALT_BYTES", "salt_bytes"),
        ("AUTH_TOKEN_BYTES", "token_bytes"),
        ("AUTH_TOKEN_TTL_SECONDS", "token_ttl_seconds"),
        ("AUTH_ISSUER", "issuer"),
        ("AUTH_PEPPER_ENV", "pepper_env"),
    )

    for attr_name, override_key in attr_map:
        if hasattr(settings_instance, attr_name):
            value = getattr(settings_instance, attr_name)
            if value is not None:
                overrides[override_key] = value

    policy_attr_map = (
        ("AUTH_PASSWORD_MIN_LENGTH", "min_length"),
        ("AUTH_PASSWORD_REQUIRE_UPPERCASE", "require_uppercase"),
        ("AUTH_PASSWORD_REQUIRE_LOWERCASE", "require_lowercase"),
        ("AUTH_PASSWORD_REQUIRE_DIGITS", "require_digits"),
        ("AUTH_PASSWORD_REQUIRE_SYMBOLS", "require_symbols"),
    )

    policy: Dict[str, Any] = {}
    for attr_name, override_key in policy_attr_map:
        if hasattr(settings_instance, attr_name):
            value = getattr(settings_instance, attr_name)
            if value is not None:
                policy[override_key] = value

    if policy:
        overrides["policy"] = policy

    return overrides


def _runtime_from_defaults() -> AuthCoreRuntime:
    overrides = _settings_overrides()
    settings = load_settings(overrides=overrides or None)
    return AuthCoreRuntime(settings)


@lru_cache(maxsize=1)
def _cached_runtime() -> AuthCoreRuntime:
    return _runtime_from_defaults()


def get_auth_core_settings() -> AuthCoreSettings:
    """Expose resolved Auth Core settings for injection."""

    return _cached_runtime().settings


def get_auth_core_runtime() -> AuthCoreRuntime:
    """Return the singleton Auth Core runtime instance."""

    return _cached_runtime()


def get_password_hasher(runtime: AuthCoreRuntime = Depends(get_auth_core_runtime)) -> AuthCoreRuntime:
    """Return the runtime to access password helper methods in dependency graphs."""

    return runtime


def hash_password(password: str, runtime: AuthCoreRuntime = Depends(get_auth_core_runtime)) -> str:
    """Hash a password using the configured Auth Core runtime."""

    return runtime.hash_password(password)


def verify_password(
    password: str,
    encoded: str,
    runtime: AuthCoreRuntime = Depends(get_auth_core_runtime),
) -> bool:
    """Verify a password against the encoded hash."""

    return runtime.verify_password(password, encoded)


def issue_token(
    subject: str,
    *,
    audience: str | None = None,
    scopes: list[str] | None = None,
    runtime: AuthCoreRuntime = Depends(get_auth_core_runtime),
) -> str:
    """Issue a signed token for the provided subject."""

    return runtime.issue_token(subject, audience=audience, scopes=scopes)


__all__ = [
    "get_auth_core_runtime",
    "get_auth_core_settings",
    "get_password_hasher",
    "hash_password",
    "verify_password",
    "issue_token",
]
