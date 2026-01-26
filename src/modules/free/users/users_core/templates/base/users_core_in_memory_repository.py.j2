"""In-memory repository for Users Core (testing/demo use only)."""

from __future__ import annotations

from typing import Dict, List, Sequence

from .models import User
from .repository import UserRepository


class InMemoryUserRepository(UserRepository):
	"""Simple repository backed by an in-memory dictionary."""

	def __init__(self, seed: Sequence[User] | None = None) -> None:
		self._users: Dict[str, User] = {user.id: user for user in (seed or [])}

	async def get_by_id(self, user_id: str) -> User | None:
		return self._users.get(user_id)

	async def get_by_email(self, email: str) -> User | None:
		for user in self._users.values():
			if user.email.lower() == email.lower():
				return user
		return None

	async def list_users(self, *, limit: int | None = None, offset: int = 0) -> Sequence[User]:
		items: List[User] = sorted(self._users.values(), key=lambda user: user.created_at, reverse=True)
		if offset:
			items = items[offset:]
		if limit is not None:
			items = items[:limit]
		return items

	async def create_user(self, user: User) -> User:
		self._users[user.id] = user
		return user

	async def update_user(self, user: User) -> User:
		if user.id not in self._users:
			raise KeyError(user.id)
		self._users[user.id] = user
		return user

	async def delete_user(self, user_id: str) -> None:
		self._users.pop(user_id, None)


__all__ = ["InMemoryUserRepository"]
