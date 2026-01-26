# Auth Core Advanced Configuration

This guide covers override hooks and integration patterns for teams that need to customise the Auth
Core module beyond the defaults described in the usage guide.

## Override Strategy

Auth Core loads configuration by merging the defaults embedded in the vendor runtime with any
runtime overrides supplied via environment variables, settings files, or the override contract. Use
the following helpers when you need programmatic control:

- `AuthCoreOverrides.apply_environment_overrides` translates RapidKit environment variables into
  dictionary overrides that are fed into `load_settings`.
- `AuthCoreOverrides.apply_settings_overrides` inspects `core.settings.Settings` and merges any
  values that were injected by the installer into the runtime defaults.
- `AuthCoreOverrides.apply_policy_overrides` provides a single place to enforce organisation level
  password policies.

You can subclass `AuthCoreOverrides` in your project to hook into these phases. Make sure you call
`super()` so the base module keeps its validation logic.

## Pepper Management

Production environments should source the signing pepper from a secrets manager instead of leaving
it in `.env`. Update `AuthCoreOverrides.resolve_pepper` to integrate with your preferred provider. A
common pattern is to fetch the secret from AWS Secrets Manager or Hashicorp Vault and memoise the
value for the lifetime of the process. The override already wraps lookups in a cached property, so
it is safe to perform I/O inside the hook.

## Multi-Tenant Support

When building white-label platforms you may need different issuers, scopes, or hashing policies per
tenant. Inject a callable into your dependency wiring that selects the appropriate overrides based
on the request context. The generated FastAPI dependencies expose the runtime instance through
`AuthCoreRuntime`, so you can replace it with a tenant-aware implementation:

```python
from fastapi import Depends
from src.modules.free.auth.core.auth.dependencies import get_runtime


def get_tenant_runtime(tenant_id: str, runtime=Depends(get_runtime)) -> AuthCoreRuntime:
    overrides = runtime.settings.to_dict()
    overrides["issuer"] = f"tenant::{tenant_id}"
    return AuthCoreRuntime(AuthCoreSettings.from_mapping(overrides))
```

Remember to update the health endpoint JSON to include tenant metadata if you expose per-tenant
runtimes.

## Rotating Hash Parameters

If you increase PBKDF2 iterations or change the digest algorithm you must re-hash existing passwords
gradually. Auth Core encodes the algorithm and iteration count in the stored hash, so you can detect
stale hashes during login and transparently upgrade them:

```python
if runtime.verify_password(candidate, stored_hash):
    latest_hash = runtime.hash_password(candidate)
    if latest_hash != stored_hash:
        repository.save_password(user_id, latest_hash)
```

Store the upgrade timestamp so you can audit long running credentials that never log in.
