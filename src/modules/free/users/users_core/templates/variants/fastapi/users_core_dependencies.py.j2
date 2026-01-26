"""FastAPI dependency providers for Users Core."""

from __future__ import annotations

from functools import lru_cache
from importlib import import_module
from typing import Any, Optional

from fastapi import Depends

from src.modules.free.users.users_core.core.users.dto import (
    UserCreateDTO,
    UserDTO,
    UserUpdateDTO,
)
from src.modules.free.users.users_core.core.users.in_memory_repository import (
    InMemoryUserRepository,
)
from src.modules.free.users.users_core.core.users.repository import UserRepository
from src.modules.free.users.users_core.core.users.service import UsersService, UsersServiceFacade
from src.modules.free.users.users_core.core.users.settings import UsersServiceSettings


def _resolve_settings_module() -> Any | None:
    candidates = (
        "src.modules.free.essentials.settings.settings",
        "src.settings",
    )
    for candidate in candidates:
        try:
            return import_module(candidate)
        except (ImportError, ModuleNotFoundError):
            continue
    return None


def _get_project_settings_instance() -> Any | None:
    module = _resolve_settings_module()
    if module is None:
        return None

    provider = getattr(module, "get_settings", None)
    if callable(provider):
        try:
            return provider()
        except Exception:  # pragma: no cover - defensive guard
            return None

    settings_cls = getattr(module, "Settings", None)
    if settings_cls is None:
        return None

    try:
        return settings_cls()  # type: ignore[call-arg]
    except Exception:  # pragma: no cover - defensive guard
        return None


@lru_cache()
def get_users_service_settings() -> UsersServiceSettings:
    overrides: dict[str, Any] = {}
    project_settings = _get_project_settings_instance()
    if project_settings is not None:
        mapping = {
            "users_allow_registration": "allow_registration",
            "users_enforce_unique_email": "enforce_unique_email",
            "users_default_locale": "default_locale",
            "users_audit_log_enabled": "audit_log_enabled",
            "users_max_results_per_page": "max_results_per_page",
            "users_passwordless_supported": "passwordless_supported",
        }
        for attr, field_name in mapping.items():
            value = getattr(project_settings, attr, None)
            if value is not None:
                overrides[field_name] = value

    settings = UsersServiceSettings(**overrides)
    settings.validate()
    return settings


@lru_cache()
def get_users_repository() -> UserRepository:
    # In-memory repository is provided as a sensible default for scaffolds/tests.
    return InMemoryUserRepository()


def get_users_service(
    settings: UsersServiceSettings = Depends(get_users_service_settings),
    repository: UserRepository = Depends(get_users_repository),
) -> UsersService:
    return UsersService(repository, settings=settings)


def get_users_service_facade(
    service: UsersService = Depends(get_users_service),
) -> UsersServiceFacade:
    return UsersServiceFacade(service)


__all__ = [
    "get_users_service_settings",
    "get_users_repository",
    "get_users_service",
    "get_users_service_facade",
    "UsersServiceSettings",
    "UsersService",
    "UsersServiceFacade",
    "UserDTO",
    "UserCreateDTO",
    "UserUpdateDTO",
]
