"""FastAPI dependency providers for Users Profiles."""

from __future__ import annotations

from functools import lru_cache
from importlib import import_module
from typing import Any, Optional

from fastapi import Depends

from src.modules.free.users.users_profiles.core.users.profiles.dto import UserProfileUpdateDTO
from src.modules.free.users.users_profiles.core.users.profiles.in_memory_repository import InMemoryUserProfileRepository
from src.modules.free.users.users_profiles.core.users.profiles.repository import UserProfileRepositoryProtocol
from src.modules.free.users.users_profiles.core.users.profiles.service import UserProfileService, UserProfileServiceFacade
from src.modules.free.users.users_profiles.core.users.profiles.settings import UserProfileSettings


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
def get_user_profile_settings() -> UserProfileSettings:
    overrides: dict[str, Any] = {}
    project_settings = _get_project_settings_instance()
    if project_settings is not None:
        mapping = {
            "users_profiles_default_timezone": "default_timezone",
            "users_profiles_max_bio_length": "max_bio_length",
            "users_profiles_avatar_max_bytes": "avatar_max_bytes",
            "users_profiles_allow_marketing_opt_in": "allow_marketing_opt_in",
            "users_profiles_social_links_limit": "social_links_limit",
            "users_profiles_default_visibility": "default_visibility",
        }
        for attr, field_name in mapping.items():
            value = getattr(project_settings, attr, None)
            if value is not None:
                overrides[field_name] = value

    settings = UserProfileSettings(**overrides)
    settings.validate()
    return settings


@lru_cache()
def get_user_profile_repository() -> UserProfileRepositoryProtocol:
    return InMemoryUserProfileRepository()


def get_user_profile_service(
    settings: UserProfileSettings = Depends(get_user_profile_settings),
    repository: UserProfileRepositoryProtocol = Depends(get_user_profile_repository),
) -> UserProfileService:
    return UserProfileService(repository, settings=settings)


def get_user_profile_service_facade(
    service: UserProfileService = Depends(get_user_profile_service),
) -> UserProfileServiceFacade:
    return UserProfileServiceFacade(service)


__all__ = [
    "get_user_profile_settings",
    "get_user_profile_repository",
    "get_user_profile_service",
    "get_user_profile_service_facade",
    "UserProfileService",
    "UserProfileServiceFacade",
    "UserProfileSettings",
    "UserProfileRepositoryProtocol",
    "InMemoryUserProfileRepository",
    "UserProfileUpdateDTO",
]
