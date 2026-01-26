# Users Profiles Module Troubleshooting

Common issues and fixes for the module.

## Profiles fail to persist

- Ensure your dependency override returns an implementation of `UserProfileRepositoryProtocol`.
- Confirm the storage driver credentials are injected before the service is constructed.
- Enable debug logging (`RAPIDKIT_LOG_LEVEL=DEBUG`) to view repository exceptions.

## Health endpoint reports `status: degraded`

The health check reads the service defaults and repository status. When the endpoint returns a
degraded state:

1. Check the generated `/src/health/users_profiles.py` handler logs.
1. Verify environment overrides (for example `RAPIDKIT_USERS_PROFILES_DEFAULT_TIMEZONE`) are valid.
1. Confirm external dependencies (database, CDN) are reachable from the runtime container.

## Avatar uploads rejected

- Increase `RAPIDKIT_USERS_PROFILES_AVATAR_MAX_BYTES` to match your front-end payloads.
- Inspect the generated upload validation in `service.py` to ensure custom MIME types are allowed.
- When using object storage, confirm temporary credentials grant write access.

## Marketing opt-in fields missing

Set `RAPIDKIT_USERS_PROFILES_ALLOW_MARKETING_OPT_IN=true` before regenerating the module. The
generator strips the fields entirely when the flag is false, so regenerate after updating the
environment.
