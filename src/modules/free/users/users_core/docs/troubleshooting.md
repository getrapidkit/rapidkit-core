# Users Core Troubleshooting

This guide covers frequent issues encountered when integrating the Users Core module.

## Health Endpoint Returns 503

**Symptom:** `/api/health/module/users-core` responds with `503 Service Unavailable` during startup.

- Confirm `RAPIDKIT_USERS_CORE_ENFORCE_UNIQUE_EMAIL` and other overrides contain valid values
  (`true`, `false`, `1`, `0`). Invalid strings fail validation and bubble up through the health
  check.
- Ensure `src.modules.free.users.users_core.core.users.settings.UsersServiceSettings` can
  instantiate. Missing environment files or broken `.env` formatting cause validation errors that
  surface through the health probe.
- If you replaced the repository implementation, verify it raises `UsersRepositoryError` for
  transient issues rather than generic exceptions so the health handler can classify the failure.

## Dependency Injection Fails in FastAPI

**Symptom:** `Depends(get_users_service)` raises `RuntimeError: UsersService not configured`.

- Call `configure_users_dependencies()` during application startup if you override the default
  repository or service implementations. The generator wires this automatically when you import the
  generated router, but custom bootstrap code may skip the helper.
- Check for circular imports in your project; the dependencies module should load before routers or
  endpoints that consume it.

## NestJS Build Errors After Upgrade

**Symptom:** `UsersCoreModule` providers fail to compile or the TypeScript build cannot resolve the
package.

- Re-run the NestJS generator to sync template changes:
  `poetry run python -m src.modules.free.users.users_core.generate nestjs ./your-output`
- Confirm `@rapidkit/users-core` (or your local path alias) resolves to the generated output folder.
- If using custom HTTP clients, update the service wrapper to match the generated interface or
  extend the provided `UsersCoreService` instead of replacing it.

## Missing Audit Logs

**Symptom:** Audit statements do not appear after user creation or updates.

- Ensure `RAPIDKIT_USERS_CORE_AUDIT_LOG_ENABLED` is set to `true` (string) in the runtime
  environment.
- Inject a logger or event sink when initialising the service facade. By default it emits to the
  module logger (`src.modules.free.users.users_core.core.users.service`); configure your logging
  handlers to forward that channel to your observability stack.
