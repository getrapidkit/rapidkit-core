"""Service layer for Users Profiles."""

from __future__ import annotations

from .dto import UserProfileReadDTO, UserProfileUpdateDTO
from .errors import ProfileNotFoundError, ProfileValidationError
from .models import ProfileVisibility
from .repository import UserProfileRepositoryProtocol
from .settings import UserProfileSettings


def _coerce_visibility(value: ProfileVisibility | str | None, default: str) -> ProfileVisibility:
	if isinstance(value, ProfileVisibility):
		return value
	if value is None:
		try:
			return ProfileVisibility(default)
		except Exception:
			return ProfileVisibility.PUBLIC
	try:
		return ProfileVisibility(str(value))
	except Exception:
		return ProfileVisibility.PUBLIC


class UserProfileService:
	def __init__(self, repository: UserProfileRepositoryProtocol, *, settings: UserProfileSettings) -> None:
		self._repository = repository
		self._settings = settings

	@property
	def settings(self) -> UserProfileSettings:
		return self._settings

	async def get_profile(self, user_id: str) -> UserProfileReadDTO:
		existing = await self._repository.get_by_user_id(user_id)
		if existing is None:
			raise ProfileNotFoundError(f"Profile for user '{user_id}' not found")
		return existing

	async def upsert_profile(self, user_id: str, payload: UserProfileUpdateDTO) -> UserProfileReadDTO:
		if payload.biography is not None and len(payload.biography) > self._settings.max_bio_length:
			raise ProfileValidationError("Biography exceeds max_bio_length")

		if payload.social_links is not None and len(payload.social_links) > self._settings.social_links_limit:
			raise ProfileValidationError("Too many social links")

		resolved_payload = payload

		if resolved_payload.timezone is None:
			resolved_payload = resolved_payload.model_copy(update={"timezone": self._settings.default_timezone})

		if resolved_payload.marketing_opt_in is None:
			resolved_payload = resolved_payload.model_copy(
				update={"marketing_opt_in": bool(self._settings.allow_marketing_opt_in)}
			)

		if resolved_payload.visibility is None:
			resolved_payload = resolved_payload.model_copy(
				update={"visibility": _coerce_visibility(None, self._settings.default_visibility)}
			)

		return await self._repository.upsert(user_id, resolved_payload)

	async def delete_profile(self, user_id: str) -> None:
		deleted = await self._repository.delete(user_id)
		if not deleted:
			raise ProfileNotFoundError(f"Profile for user '{user_id}' not found")


class UserProfileServiceFacade:
	"""Small facade to keep the HTTP adapter surface stable."""

	def __init__(self, service: UserProfileService) -> None:
		self._service = service

	async def get_profile(self, user_id: str) -> UserProfileReadDTO:
		return await self._service.get_profile(user_id)

	async def upsert_profile(self, user_id: str, payload: UserProfileUpdateDTO) -> UserProfileReadDTO:
		return await self._service.upsert_profile(user_id, payload)

	async def delete_profile(self, user_id: str) -> None:
		await self._service.delete_profile(user_id)
