"""DTOs for Users Profiles HTTP adapters."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .models import ProfileVisibility


class UserProfileUpdateDTO(BaseModel):
	"""Payload accepted when creating/updating a profile."""

	display_name: Optional[str] = Field(default=None, max_length=200)
	avatar_url: Optional[str] = Field(default=None, max_length=2048)
	timezone: Optional[str] = Field(default=None, max_length=64)
	biography: Optional[str] = Field(default=None)
	social_links: Optional[list[str]] = Field(default=None)
	marketing_opt_in: Optional[bool] = Field(default=None)
	visibility: Optional[ProfileVisibility] = Field(default=None)


class UserProfileReadDTO(BaseModel):
	"""Profile DTO returned by HTTP endpoints."""

	user_id: str = Field(..., min_length=1)
	display_name: Optional[str] = Field(default=None)
	avatar_url: Optional[str] = Field(default=None)
	timezone: str = Field(default="UTC")
	biography: Optional[str] = Field(default=None)
	social_links: list[str] = Field(default_factory=list)
	marketing_opt_in: bool = Field(default=True)
	visibility: ProfileVisibility = Field(default=ProfileVisibility.PUBLIC)
	created_at: datetime
	updated_at: datetime
