"""Settings model for Users Profiles."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UserProfileSettings:
	default_timezone: str = "UTC"
	max_bio_length: int = 280
	avatar_max_bytes: int = 2_097_152
	allow_marketing_opt_in: bool = True
	social_links_limit: int = 5
	default_visibility: str = "public"

	def validate(self) -> None:
		if self.max_bio_length < 0:
			raise ValueError("max_bio_length must be >= 0")
		if self.avatar_max_bytes < 0:
			raise ValueError("avatar_max_bytes must be >= 0")
		if self.social_links_limit < 0:
			raise ValueError("social_links_limit must be >= 0")
		if not self.default_timezone:
			raise ValueError("default_timezone must not be empty")
		if not self.default_visibility:
			raise ValueError("default_visibility must not be empty")
