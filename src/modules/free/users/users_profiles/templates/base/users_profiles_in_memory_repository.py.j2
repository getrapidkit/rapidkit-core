"""In-memory repository implementation for Users Profiles."""

from __future__ import annotations

from datetime import datetime, timezone

from .dto import UserProfileReadDTO, UserProfileUpdateDTO
from .models import ProfileVisibility
from .repository import UserProfileRepositoryProtocol


def _utc_now() -> datetime:
	return datetime.now(timezone.utc)


class InMemoryUserProfileRepository(UserProfileRepositoryProtocol):
	def __init__(self) -> None:
		self._profiles: dict[str, UserProfileReadDTO] = {}

	async def get_by_user_id(self, user_id: str) -> UserProfileReadDTO | None:
		return self._profiles.get(user_id)

	async def upsert(self, user_id: str, payload: UserProfileUpdateDTO) -> UserProfileReadDTO:
		existing = self._profiles.get(user_id)
		now = _utc_now()

		created_at = existing.created_at if existing is not None else now

		profile = UserProfileReadDTO(
			user_id=user_id,
			display_name=payload.display_name if payload.display_name is not None else (existing.display_name if existing else None),
			avatar_url=payload.avatar_url if payload.avatar_url is not None else (existing.avatar_url if existing else None),
			timezone=payload.timezone if payload.timezone is not None else (existing.timezone if existing else "UTC"),
			biography=payload.biography if payload.biography is not None else (existing.biography if existing else None),
			social_links=list(payload.social_links) if payload.social_links is not None else (list(existing.social_links) if existing else []),
			marketing_opt_in=payload.marketing_opt_in if payload.marketing_opt_in is not None else (existing.marketing_opt_in if existing else True),
			visibility=payload.visibility if payload.visibility is not None else (existing.visibility if existing else ProfileVisibility.PUBLIC),
			created_at=created_at,
			updated_at=now,
		)

		self._profiles[user_id] = profile
		return profile

	async def delete(self, user_id: str) -> bool:
		return self._profiles.pop(user_id, None) is not None
