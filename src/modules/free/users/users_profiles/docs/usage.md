# Users Profiles Module Usage

Follow this guide to generate the module, wire it into your application, and control it through
environment variables.

## Generate the module assets

Render the vendor runtime plus the desired framework variant. The generator writes into the target
directory you provide.

```bash
# FastAPI project (writes into the current directory)
poetry run python -m src.modules.free.users.users_profiles.generate fastapi .

# NestJS example project
poetry run python -m src.modules.free.users.users_profiles.generate nestjs ./examples/users_profiles-nest
```

If you already run `rapidkit modules lock`, re-run it after generation so vendor snapshots stay in
sync.

## FastAPI integration

The FastAPI variant exposes dependencies and routers under
`src.modules.free.users.users_profiles.core.users.profiles`. Typical usage looks like this:

```python
from fastapi import APIRouter, Depends
from src.modules.free.users.users_profiles.core.users.profiles.service import (
    UserProfileService,
)
from src.modules.free.users.users_profiles.core.users.profiles.dependencies import (
    get_user_profile_service,
    CreateProfileRequest,
)

router = APIRouter(prefix="/users/{user_id}/profile", tags=["profiles"])


@router.post("", status_code=201)
async def create_profile(
    user_id: str,
    payload: CreateProfileRequest,
    service: UserProfileService = Depends(get_user_profile_service),
):
    return await service.create_profile(user_id, payload)


@router.get("", response_model=UserProfileService.model_type)
async def get_profile(
    user_id: str,
    service: UserProfileService = Depends(get_user_profile_service),
):
    return await service.get_profile(user_id)
```

Mount the router on your FastAPI application and the health check endpoint
(`/api/health/module/users_profiles`) becomes available automatically.

## NestJS integration

The NestJS variant ships a module, controller, and service in `src/users_profiles`. Import the
module into your main application module:

```typescript
import { Module } from '@nestjs/common';
import { UsersProfilesModule } from './users_profiles/users_profiles.module';

@Module({
  imports: [UsersProfilesModule],
})
export class AppModule {}
```

The generated service proxies to the shared runtime helpers, so overrides stay consistent across
frameworks.

## Environment variables

Tune behaviour without forking templates by setting the following variables (all optional):

| Variable                                         | Description                                                |
| ------------------------------------------------ | ---------------------------------------------------------- |
| `RAPIDKIT_USERS_PROFILES_DEFAULT_TIMEZONE`       | Default timezone applied when profiles omit one.           |
| `RAPIDKIT_USERS_PROFILES_MAX_BIO_LENGTH`         | Maximum biography length (characters).                     |
| `RAPIDKIT_USERS_PROFILES_AVATAR_MAX_BYTES`       | Max avatar upload size (bytes).                            |
| `RAPIDKIT_USERS_PROFILES_ALLOW_MARKETING_OPT_IN` | Toggle marketing preference fields.                        |
| `RAPIDKIT_USERS_PROFILES_SOCIAL_LINKS_LIMIT`     | Cap the number of social links stored per profile.         |
| `RAPIDKIT_USERS_PROFILES_DEFAULT_VISIBILITY`     | Default visibility state (`public`, `private`, or `team`). |

Restart the generator after changing these values so they flow into the rendered code.
