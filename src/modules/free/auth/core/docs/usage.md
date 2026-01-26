# Auth Core Module Usage Guide

The Auth Core module delivers deterministic password hashing and HMAC token helpers for RapidKit
projects. It also wires health probes and FastAPI dependencies so applications can adopt shared
security primitives with minimal boilerplate.

## 1. Generate Artefacts

```bash
rapidkit add module auth_core
rapidkit modules lock --overwrite
```

The generator publishes vendor sources under `.rapidkit/vendor/auth_core/<version>` and renders the
framework-specific assets into your project (`src/modules/free/auth/core/`, and test scaffolding).
Re-run the generator manually when iterating on templates:

```bash
poetry run python -m src.modules.free.auth.core.generate fastapi .
poetry run python -m src.modules.free.auth.core.generate nestjs ./examples/auth-core-nest
```

## 2. Configure Environment Defaults

| Variable                        | Description                                                                 |
| ------------------------------- | --------------------------------------------------------------------------- |
| `RAPIDKIT_AUTH_CORE_PEPPER`     | HMAC signing pepper used when issuing tokens. Generate with `openssl rand`. |
| `RAPIDKIT_AUTH_CORE_HASH`       | Optional override for the PBKDF2 digest (default `sha256`).                 |
| `RAPIDKIT_AUTH_CORE_ITERATIONS` | Global override for PBKDF2 iterations.                                      |
| `RAPIDKIT_AUTH_CORE_TOKEN_TTL`  | Override the default token lifetime in seconds.                             |
| `RAPIDKIT_AUTH_CORE_ISSUER`     | Override issuer claim embedded in generated tokens.                         |
| `RAPIDKIT_AUTH_CORE_POLICY`     | JSON payload overriding password policy fields.                             |

After installation the `.env` template includes a placeholder pepper entry. Replace it with a strong
secret before deploying:

```bash
# Example: 48 random bytes encoded in Base64
export RAPIDKIT_AUTH_CORE_PEPPER="$(openssl rand -base64 48)"
```

## 3. FastAPI Integration

```python
from fastapi import APIRouter, Depends
from src.modules.free.auth.core.auth.dependencies import (
    hash_password,
    verify_password,
    issue_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register_user(password: str, hasher=Depends(hash_password)) -> dict[str, str]:
    encoded = hasher(password)
    # store the hash and return a success response
    return {"password_hash": encoded}


@router.post("/login")
async def login_user(
    password: str,
    stored_hash: str,
    checker=Depends(verify_password),
    token_factory=Depends(issue_token),
) -> dict[str, str]:
    if not checker(password, stored_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"access_token": token_factory("user-id-123", scopes=["api"])}
```

The dependency helpers cache a singleton runtime so hashing and signing remain deterministic during
the process lifetime.

## 4. Settings Integration

Module installers now inject the following fields into
`src.modules.free.essentials.settings.settings.Settings`:

- `AUTH_HASH_NAME`, `AUTH_HASH_ITERATIONS`, `AUTH_SALT_BYTES`
- `AUTH_TOKEN_BYTES`, `AUTH_TOKEN_TTL_SECONDS`, `AUTH_ISSUER`, `AUTH_PEPPER_ENV`
- `AUTH_PASSWORD_MIN_LENGTH`, `AUTH_PASSWORD_REQUIRE_UPPERCASE`, `AUTH_PASSWORD_REQUIRE_LOWERCASE`
- `AUTH_PASSWORD_REQUIRE_DIGITS`, `AUTH_PASSWORD_REQUIRE_SYMBOLS`

Populate these through environment variables or configuration files. The dependency helpers detect
non-null values and feed them into `load_settings(overrides=...)`, letting you fine-tune Auth Core
without touching the vendor runtime.

## 5. Health Endpoints

The module registers `/api/health/module/auth-core`. Include it by calling `register_health_routes`
from `src.health.auth_core` or `register_auth_core_health` directly. The payload surfaces the
hashing algorithm, iteration count, issuer, and whether a signing pepper is configured.

## 6. Testing

Generated projects receive `tests/modules/free_auth_core/test_auth_core_runtime.py` alongside the
generator regression tests. Run the Auth Core suite together with the rest of your tests:

```bash
poetry run pytest tests/modules/free_auth_core -q
```

Refer to `docs/troubleshooting.md` if you observe warnings about missing peppers or signature
verification failures.
