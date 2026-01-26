# Passwordless Module Usage Guide

## 1. Install and Generate

```bash
rapidkit add module passwordless
rapidkit modules lock --overwrite
```

The generator produces runtime helpers under `src/modules/free/auth/passwordless/passwordless.py`,
FastAPI scaffolding, and a NestJS service. Vendor code lands in
`.rapidkit/vendor/passwordless/<version>` for auditing.

## 2. Configure Delivery Backend

The runtime exposes `PasswordlessRuntime` with `issue_code()` and `verify_code()` helpers. Inject
the `send_code` callback when wiring your application so the module remains transport agnostic.

```python
from src.modules.free.auth.passwordless.passwordless import (
    PasswordlessRuntime,
    load_passwordless_settings,
)

runtime = PasswordlessRuntime(load_passwordless_settings({"token_ttl_seconds": 600}))
token = runtime.issue_code("user@example.com", delivery_method="email")
email_service.send_magic_link(user.email, code=token.code, token=token.token_id)
```

Store the verification token in your chosen cache (Redis, DynamoDB, etc.) together with the issued
code. When the user returns, call `runtime.verify_code()` to validate the presented credentials and
clean up the stored entry.

## 3. Framework Integration

The FastAPI router stub includes `/passwordless/health` and `/passwordless/verify`. Replace the
placeholder logic with your persistence layer and call the runtime helpers to validate submissions.

The NestJS artefacts expose the same API surface; inject your delivery and persistence services via
NestJS providers.

## 4. Testing

Run the provided smoke tests whenever you change expiration rules or persistence logic:

```bash
poetry run pytest tests/modules/free_auth_passwordless -q
```

Extend the suite with transport-specific mocks so delivery failures are detected during CI.
