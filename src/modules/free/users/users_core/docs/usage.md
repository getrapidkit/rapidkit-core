# Users Core Module Usage Guide

The Users Core module delivers reusable user lifecycle services, DTOs, and HTTP adapters. Follow the
steps below to scaffold the module, configure environment knobs, and expose the runtime through
FastAPI or NestJS applications.

## 1. Generate Artefacts

```bash
rapidkit add module users_core
rapidkit modules lock --overwrite
```

The generator emits vendor sources under `.rapidkit/vendor/users_core/<version>` and renders the
active framework variant into your project tree. Re-run the generator manually when iterating on
templates or switching frameworks:

```bash
poetry run python -m src.modules.free.users.users_core.generate fastapi .
poetry run python -m src.modules.free.users.users_core.generate nestjs ./examples/users-core-nest
```

## 2. Configure Environment Defaults

Override default behaviour through environment variables before launching your service:

| Variable                                     | Description                                                       |
| -------------------------------------------- | ----------------------------------------------------------------- |
| `RAPIDKIT_USERS_CORE_ALLOW_REGISTRATION`     | Toggle self-service registration flows (`true`/`false`).          |
| `RAPIDKIT_USERS_CORE_ENFORCE_UNIQUE_EMAIL`   | Enforce uniqueness at the service layer.                          |
| `RAPIDKIT_USERS_CORE_DEFAULT_LOCALE`         | Global fallback locale (for welcome emails, audit logs, etc.).    |
| `RAPIDKIT_USERS_CORE_AUDIT_LOG_ENABLED`      | Enable audit log emission for create/update events.               |
| `RAPIDKIT_USERS_CORE_MAX_RESULTS_PER_PAGE`   | Default page size for directory searches (preferred, new name).   |
| `RAPIDKIT_USERS_CORE_MAX_RESULTS`            | Legacy name for default page size; still supported as a fallback. |
| `RAPIDKIT_USERS_CORE_PASSWORDLESS_SUPPORTED` | Advertise passwordless readiness to clients.                      |

Generated `.env` templates include these keys; update values per environment (development, staging,
production) and commit sanitised defaults only.

## 3. FastAPI Integration

```python
from fastapi import APIRouter, Depends, HTTPException
from src.modules.free.users.users_core.core.users.dependencies import get_users_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}")
async def fetch_user(user_id: str, service=Depends(get_users_service)) -> dict:
    user = service.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user.model_dump()


@router.post("/")
async def create_user(payload: dict, service=Depends(get_users_service)) -> dict:
    created = service.create_user(payload)
    return created.model_dump()
```

Mount the generated router (`src.modules.free.users.users_core.core.users.router`) if you prefer the
out-of-the-box REST surface. The dependency helpers cache a configured `UsersServiceFacade`,
honouring the environment overrides described above.

## 4. NestJS Integration

```typescript
import { UsersCoreService } from "@rapidkit/users-core";

@Controller("users")
export class UsersController {
  constructor(private readonly usersService: UsersCoreService) {}

  @Get(":id")
  async fetch(@Param("id") id: string) {
    const user = await this.usersService.getUser(id);
    if (!user) {
      throw new NotFoundException();
    }
    return user;
  }
}
```

The generated NestJS module exports providers that mirror the Python service contract, enabling
hybrid platform deployments.

## 5. Health Endpoints

Call `register_users_core_health(app)` or the shared `register_health_routes(app)` helper to expose
`/api/health/module/users-core`. The route validates configuration and returns the current defaults
so observability dashboards can flag misconfiguration early.

## Notes on health helpers (canonical-only)

Vendor health runtimes are packaged in the vendor snapshot (e.g.
`.rapidkit/vendor/<module>/<version>/...`). Generated projects expose a canonical public shim at
`src/health/<module>.py`. Under the canonical-only policy the generator does not emit legacy health
compatibility aliases — projects and templates should import health registrars from
`src.health.<module>`.

## 6. Testing

Regressions for the generator, overrides, CLI entrypoint, and plugin wiring live under
`tests/modules/free/users/core/`. Ensure they pass alongside your application test suite:

```bash
poetry run pytest tests/modules/free/users/core -q
```

Extend the in-memory repository or swap it with your production persistence layer inside your test
fixtures to match project-specific requirements.
