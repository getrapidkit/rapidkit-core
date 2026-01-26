"""Data transfer objects for Users Core."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator

from .models import User, UserStatus


class UserDTO(BaseModel):
	"""Serializable representation of a user."""

	id: str
	email: EmailStr
	full_name: Optional[str]
	locale: str
	status: UserStatus
	is_verified: bool
	metadata: dict[str, str] | None = None
	created_at: datetime
	updated_at: datetime

	@classmethod
	def from_entity(cls, entity: User) -> "UserDTO":
		return cls.model_validate(entity.model_dump())


class UserCreateDTO(BaseModel):
	"""Incoming payload for creating a user."""

	email: EmailStr
	full_name: Optional[str] = None
	locale: str = Field(default="en", min_length=2, max_length=10)
	is_verified: bool = False
	metadata: dict[str, str] | None = None


class UserUpdateDTO(BaseModel):
	"""Incoming payload for updating mutable user fields."""

	full_name: Optional[str] = None
	locale: Optional[str] = Field(default=None, min_length=2, max_length=10)
	status: Optional[UserStatus] = None
	is_verified: Optional[bool] = None
	metadata: Optional[dict[str, str]] = None

	@validator("metadata")
	def _sanitize_metadata(cls, value: Optional[dict[str, str]]) -> Optional[dict[str, str]]:  # noqa: D401
		if value is None:
			return value
		return {str(key): str(val) for key, val in value.items()}


__all__ = ["UserDTO", "UserCreateDTO", "UserUpdateDTO"]
