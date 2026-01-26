# Users Profiles Module Advanced Topics

Peek under the hood of the Users Profiles module to extend the default behaviour without diverging
from upstream templates.

## Plug in a custom repository

Implement `UserProfileRepositoryProtocol` and register it in the generated dependency override to
back the service with your storage layer.

```python
from typing import Iterable
from src.modules.free.users.users_profiles.core.users.profiles import (
    UserProfile,
    UserProfileRepositoryProtocol,
)


class PostgresProfileRepository(UserProfileRepositoryProtocol):
    def __init__(self, pool) -> None:
        self._pool = pool

    async def create_profile(self, profile: UserProfile) -> UserProfile:
        await self._pool.execute("INSERT ...", profile.model_dump())
        return profile

    async def get_profile(self, user_id: str) -> UserProfile | None:
        row = await self._pool.fetchrow(
            "SELECT * FROM profiles WHERE user_id = $1", user_id
        )
        return UserProfile.model_validate(row) if row else None

    async def list_profiles(self) -> Iterable[UserProfile]:
        rows = await self._pool.fetch("SELECT * FROM profiles")
        for row in rows:
            yield UserProfile.model_validate(row)
```

Update `src/modules/free/users/users_profiles/core/users/profiles/dependencies.py` in your project
to return the custom repository.

## Use overrides for tenant-specific defaults

`UsersProfileOverrides` reads the `RAPIDKIT_USERS_PROFILES_*` environment variables during
generation. Compose multiple builds with distinct defaults by exporting values before each run:

```bash
RAPIDKIT_USERS_PROFILES_DEFAULT_VISIBILITY=team \
RAPIDKIT_USERS_PROFILES_SOCIAL_LINKS_LIMIT=15 \
poetry run python -m src.modules.free.users.users_profiles.generate fastapi ./build/team
```

Every render persists the defaults directly into the runtime config so your deployments stay
deterministic.

## Extend health telemetry

Call `describe_users_profiles(extras=...)` from application startup to append domain-specific
diagnostics (for example, storage latency or CDN errors). The returned dictionary feeds the health
endpoint, keeping operations teams informed without modifying vendor files.

```python
from src.modules.free.users.users_profiles.core.users.profiles import (
    describe_users_profiles,
)

health_payload = describe_users_profiles(
    extras={("profile_datastore", "postgresql"), ("avatar_cdn", "s3")}
)
```

## Enforce privacy policies centrally

The generated service already takes visibility and marketing flags into account. For bespoke privacy
rules, inherit from `UserProfileService`, override the relevant methods, and swap the service in
your dependency container. Because the service constructor only depends on the repository and
settings, extending it preserves compatibility with future releases.
