# Users Profiles Module Overview

The Users Profiles module extends Users Core with rich profile metadata, avatar management, social
links, and privacy controls for personalised user experiences across FastAPI and NestJS
applications.

## Key Capabilities

- **Profile domain models** – Pydantic-based biographies, social links, time zones, and visibility
  controls.
- **Service orchestration** – `UserProfileService` coordinates persistence, validation, and
  user-existence checks with async APIs.
- **Repository protocol** – Pluggable persistence via `UserProfileRepositoryProtocol` with in-memory
  implementation for testing.
- **Framework adapters** – FastAPI dependency providers and routers plus NestJS service mirror for
  polyglot teams.
- **Health telemetry** – `/api/health/module/users_profiles` surfaces configuration state and
  repository reachability.
- **Vendor separation** – Upgrade-safe architecture with vendor snapshots in `.rapidkit/vendor`
  directory.

## Module Components

- **Profile Domain**: Pydantic models for user profile data
- **Profile Service**: Business logic layer with validation
- **Repository Protocol**: Pluggable persistence abstraction
- **Health Checks**: Configuration and repository monitoring
- **Framework Adapters**: FastAPI routers and NestJS services

## Architecture

```
┌──────────────────┐
│  Application     │
└──────────────────┘
         │
    ┌────────────────────┐
    │  Profile Service   │ ← Business logic
    └────────────────────┘
         │
    ┌────────────────────┐
    │  Repository        │ ← Persistence
    │  Protocol          │
    └────────────────────┘
         │
    ┌────────────────────┐
    │  Database          │
    └────────────────────┘
```

## Quick Start

### FastAPI

```python
from fastapi import FastAPI, Depends
from rapidkit.runtime.users.profiles import (
    UserProfileService,
    get_profile_service,
    CreateProfileRequest,
)

app = FastAPI()


@app.post("/users/{user_id}/profile")
async def create_profile(
    user_id: str,
    data: CreateProfileRequest,
    service: UserProfileService = Depends(get_profile_service),
):
    profile = await service.create_profile(user_id, data)
    return profile


@app.get("/users/{user_id}/profile")
async def get_profile(
    user_id: str, service: UserProfileService = Depends(get_profile_service)
):
    profile = await service.get_profile(user_id)
    return profile
```

### NestJS

```typescript
import { Injectable } from '@nestjs/common';
import { UserProfileService } from './profiles/profiles.service';

@Injectable()
export class UsersService {
  constructor(private profileService: UserProfileService) {}

  async createProfile(userId: string, data: CreateProfileDto) {
    return await this.profileService.createProfile(userId, data);
  }

  async getProfile(userId: string) {
    return await this.profileService.getProfile(userId);
  }
}
```

## Configuration

Environment variables:

```bash
RAPIDKIT_USERS_PROFILES_DEFAULT_TIMEZONE=UTC
RAPIDKIT_USERS_PROFILES_MAX_BIO_LENGTH=500
RAPIDKIT_USERS_PROFILES_AVATAR_MAX_BYTES=5242880
RAPIDKIT_USERS_PROFILES_ALLOW_MARKETING_OPT_IN=true
RAPIDKIT_USERS_PROFILES_SOCIAL_LINKS_LIMIT=10
RAPIDKIT_USERS_PROFILES_DEFAULT_VISIBILITY=public
```

## Profile Data Model

```python
from rapidkit.runtime.users.profiles import UserProfile

profile = UserProfile(
    user_id="user_123",
    display_name="Alice",
    bio="Software engineer and coffee enthusiast",
    avatar_url="https://cdn.example.com/avatars/alice.jpg",
    timezone="America/New_York",
    social_links=[
        {"platform": "twitter", "url": "https://twitter.com/alice"},
        {"platform": "github", "url": "https://github.com/alice"},
    ],
    marketing_opt_in=True,
    visibility="public",  # public, private, friends_only
)
```

## Repository Implementation

Custom persistence layer:

```python
from rapidkit.runtime.users.profiles import UserProfileRepositoryProtocol


class PostgresProfileRepository(UserProfileRepositoryProtocol):
    async def create(self, profile: UserProfile) -> UserProfile:
        # Insert into database
        pass

    async def get_by_user_id(self, user_id: str) -> UserProfile | None:
        # Fetch from database
        pass

    async def update(self, user_id: str, data: dict) -> UserProfile:
        # Update database record
        pass

    async def delete(self, user_id: str) -> bool:
        # Delete from database
        pass
```

## Profile Validation

Built-in validation rules:

- **Biography length**: Configurable max characters
- **Avatar size**: Max file size in bytes
- **Social links**: URL format validation and count limits
- **Time zone**: Valid IANA time zone strings
- **Visibility**: Enum validation (public/private/friends_only)

## Privacy Controls

```python
# Set profile visibility
await service.update_profile(user_id="user_123", data={"visibility": "private"})

# Marketing opt-in/out
await service.update_profile(user_id="user_123", data={"marketing_opt_in": False})
```

## Health Monitoring

Health endpoint provides:

- Configuration validation status
- Repository connectivity
- Profile count statistics
- Default settings

```json
{
  "status": "healthy",
  "module": "users_profiles",
  "configuration": {
    "max_bio_length": 500,
    "avatar_max_bytes": 5242880,
    "social_links_limit": 10,
    "default_visibility": "public"
  },
  "repository": {
    "connected": true,
    "total_profiles": 1234
  }
}
```

Access at `/api/health/module/users_profiles`.

## Testing Support

In-memory repository for tests:

```python
from rapidkit.runtime.users.profiles.testing import InMemoryProfileRepository

repository = InMemoryProfileRepository()
service = UserProfileService(repository)

# Use in tests without database
profile = await service.create_profile("user_123", data)
assert profile.user_id == "user_123"
```

## Supported Frameworks

- **FastAPI**: Full async support with dependency injection
- **NestJS**: Injectable service with TypeScript definitions
- **Custom**: Direct service instantiation for other frameworks

## Integration with Users Core

Profiles module extends Users Core:

```python
from rapidkit.runtime.users.core import get_user_service
from rapidkit.runtime.users.profiles import get_profile_service

# Verify user exists before creating profile
user = await user_service.get_user(user_id)
if user:
    profile = await profile_service.create_profile(user_id, data)
```

## Performance Features

- **Lazy loading**: Load profiles only when needed
- **Caching**: Optional profile caching with Redis
- **Batch operations**: Bulk profile fetching
- **Index optimization**: Database indexes on user_id

## Security Features

- **Input validation**: Pydantic model validation
- **XSS prevention**: Sanitize user-provided content
- **URL validation**: Verify social link URLs
- **Privacy enforcement**: Respect visibility settings

## Getting Help

- **Overview**: This document
- **Module README**: `src/modules/free/users/users_profiles/README.md`

For issues and questions, visit our [GitHub repository](https://github.com/getrapidkit/core).
