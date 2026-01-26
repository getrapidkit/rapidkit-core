"""Domain models for Users Profiles."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


def utc_now() -> datetime:
	return datetime.now(timezone.utc)


class ProfileVisibility(str, Enum):
	PUBLIC = "public"
	PRIVATE = "private"
	TEAM = "team"


class UserProfile(BaseModel):
	"""Aggregate describing a user's profile."""

	user_id: str = Field(..., min_length=1)
	display_name: Optional[str] = Field(default=None, max_length=200)
	avatar_url: Optional[str] = Field(default=None, max_length=2048)
	timezone: str = Field(default="UTC", min_length=1, max_length=64)
	biography: Optional[str] = Field(default=None)
	social_links: list[str] = Field(default_factory=list)
	marketing_opt_in: bool = Field(default=True)
	visibility: ProfileVisibility = Field(default=ProfileVisibility.PUBLIC)
	created_at: datetime = Field(default_factory=utc_now)
	updated_at: datetime = Field(default_factory=utc_now)

	class Config:
		frozen = True
