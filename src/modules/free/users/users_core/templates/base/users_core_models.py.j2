"""Domain models for Users Core."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(timezone.utc)


class UserStatus(str, Enum):
    """Lifecycle state of a user within the system."""

    ACTIVE = "active"
    INVITED = "invited"
    DISABLED = "disabled"


class User(BaseModel):
    """Aggregate root describing a user account."""

    id: str = Field(..., description="Stable unique identifier for the user")
    email: EmailStr = Field(..., description="Primary email address")
    full_name: Optional[str] = Field(default=None, description="Display name")
    locale: str = Field(default="en", min_length=2, max_length=10, description="Locale code")
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="Current lifecycle status")
    is_verified: bool = Field(default=False, description="Whether the user verified their email")
    metadata: dict[str, str] | None = Field(default=None, description="Extensible metadata")
    created_at: datetime = Field(default_factory=utc_now, description="Creation timestamp (UTC)")
    updated_at: datetime = Field(default_factory=utc_now, description="Last modification timestamp (UTC)")

    class Config:
        frozen = True
        json_encoders = {datetime: lambda value: value.isoformat()}  # noqa: E731
        orm_mode = True


__all__ = ["User", "UserStatus", "utc_now"]
