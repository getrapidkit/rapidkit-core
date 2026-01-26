"""Repository abstractions for Users Core."""

from __future__ import annotations

from typing import Protocol, Sequence

from .models import User


class UserRepository(Protocol):
    """Repository contract describing persistence operations."""

    async def get_by_id(self, user_id: str) -> User | None:
        """Return a user by identifier."""

    async def get_by_email(self, email: str) -> User | None:
        """Return a user by email if it exists."""

    async def list_users(self, *, limit: int | None = None, offset: int = 0) -> Sequence[User]:
        """Return a slice of users ordered by creation date descending."""

    async def create_user(self, user: User) -> User:
        """Persist a newly created user entity."""

    async def update_user(self, user: User) -> User:
        """Persist updates to an existing user entity."""

    async def delete_user(self, user_id: str) -> None:
        """Remove a user from persistence."""


__all__ = ["UserRepository"]
