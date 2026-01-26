"""Service layer orchestrating Users Core workflows."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Callable, Sequence

from pydantic import EmailStr

from .dto import UserCreateDTO, UserDTO, UserUpdateDTO
from .errors import (
    UserAlreadyExistsError,
    UserEmailConflictError,
    UserNotFoundError,
    UserRegistrationDisabledError,
)
from .models import User, UserStatus, utc_now
from .repository import UserRepository
from .settings import UsersServiceSettings

IdGenerator = Callable[[], str]
Clock = Callable[[], datetime]


def _default_id_generator() -> str:
    return uuid.uuid4().hex


def _default_clock() -> datetime:
    return utc_now()


class UsersService:
    """High-level orchestrator responsible for user lifecycle operations."""

    def __init__(
        self,
        repository: UserRepository,
        *,
        settings: UsersServiceSettings | None = None,
        id_generator: IdGenerator | None = None,
        clock: Clock | None = None,
    ) -> None:
        self._repository = repository
        self._settings = settings or UsersServiceSettings()
        self._settings.validate()
        self._id_generator = id_generator or _default_id_generator
        self._clock = clock or _default_clock

    @property
    def settings(self) -> UsersServiceSettings:
        return self._settings

    async def list_users(self, *, limit: int | None = None, offset: int = 0) -> Sequence[User]:
        if limit is None:
            limit = self._settings.max_results_per_page
        if limit <= 0:
            raise ValueError("limit must be positive")
        if offset < 0:
            raise ValueError("offset cannot be negative")
        return await self._repository.list_users(limit=limit, offset=offset)

    async def get_user(self, user_id: str) -> User:
        entity = await self._repository.get_by_id(user_id)
        if entity is None:
            raise UserNotFoundError(f"User '{user_id}' was not found")
        return entity

    async def get_user_by_email(self, email: EmailStr) -> User:
        entity = await self._repository.get_by_email(str(email))
        if entity is None:
            raise UserNotFoundError(f"User with email '{email}' was not found")
        return entity

    async def create_user(self, payload: UserCreateDTO) -> User:
        if not self._settings.allow_registration:
            raise UserRegistrationDisabledError("User registrations are disabled")

        await self._ensure_email_unique(payload.email)

        user_id = self._id_generator()
        now = self._clock()
        entity = User(
            id=user_id,
            email=payload.email,
            full_name=payload.full_name,
            locale=payload.locale or self._settings.default_locale,
            status=UserStatus.ACTIVE,
            is_verified=payload.is_verified,
            metadata=payload.metadata,
            created_at=now,
            updated_at=now,
        )
        created = await self._repository.create_user(entity)
        if created.id != user_id:
            raise UserAlreadyExistsError(
                "Repository returned mismatched identifier during create operation"
            )
        return created

    async def update_user(self, user_id: str, payload: UserUpdateDTO) -> User:
        current = await self.get_user(user_id)

        if payload.status is not None and payload.status == UserStatus.INVITED:
            raise ValueError("Cannot revert a persisted user back to invited status")

        if payload.metadata is not None:
            payload.metadata = {str(k): str(v) for k, v in payload.metadata.items()}

        if payload.locale is not None and not payload.locale:
            raise ValueError("locale cannot be an empty string")

        updated = current.model_copy(
            update={
                "full_name": payload.full_name if payload.full_name is not None else current.full_name,
                "locale": payload.locale if payload.locale is not None else current.locale,
                "status": payload.status if payload.status is not None else current.status,
                "is_verified": payload.is_verified if payload.is_verified is not None else current.is_verified,
                "metadata": payload.metadata if payload.metadata is not None else current.metadata,
                "updated_at": self._clock(),
            }
        )

        return await self._repository.update_user(updated)

    async def delete_user(self, user_id: str) -> None:
        await self.get_user(user_id)
        await self._repository.delete_user(user_id)

    async def _ensure_email_unique(self, email: EmailStr) -> None:
        if not self._settings.enforce_unique_email:
            return
        existing = await self._repository.get_by_email(str(email))
        if existing is not None:
            raise UserEmailConflictError(f"Email '{email}' already exists")


class UsersServiceFacade:
    """Convenience wrapper returning DTOs for external consumers."""

    def __init__(self, service: UsersService) -> None:
        self._service = service

    async def list_users(self, *, limit: int | None = None, offset: int = 0) -> Sequence[UserDTO]:
        entities = await self._service.list_users(limit=limit, offset=offset)
        return [UserDTO.from_entity(entity) for entity in entities]

    async def get_user(self, user_id: str) -> UserDTO:
        entity = await self._service.get_user(user_id)
        return UserDTO.from_entity(entity)

    async def create_user(self, payload: UserCreateDTO) -> UserDTO:
        entity = await self._service.create_user(payload)
        return UserDTO.from_entity(entity)

    async def update_user(self, user_id: str, payload: UserUpdateDTO) -> UserDTO:
        entity = await self._service.update_user(user_id, payload)
        return UserDTO.from_entity(entity)

    async def delete_user(self, user_id: str) -> None:
        await self._service.delete_user(user_id)


__all__ = ["UsersService", "UsersServiceSettings", "UsersServiceFacade"]
