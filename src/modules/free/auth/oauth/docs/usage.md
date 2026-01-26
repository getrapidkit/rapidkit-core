# OAuth Module Usage Guide

Use this guide to connect the generated OAuth scaffolding to your identity providers.

## 1. Install the Module

```bash
rapidkit add module oauth
rapidkit modules lock --overwrite
```

The generator renders runtime assets into `src/modules/free/auth/oauth/oauth.py`, vendor code into
`.rapidkit/vendor/oauth/<version>`, and a FastAPI router stub in
`src/modules/free/auth/oauth/routers/oauth.py`.

## 2. Configure Providers

Populate `src/auth/oauth.py` with provider information. The generated `OAuthProviderConfig`
structure expects the following fields:

- `client_id`
- `client_secret`
- `authorize_endpoint`
- `token_endpoint`
- `scope`

Store secrets in your preferred secrets manager and surface them via environment variables inside
`get_provider_registry()`.

## 3. FastAPI Integration

The generated router exposes `create_router()`; mount it under a prefix to provide health and
callback routes.

```python
from fastapi import FastAPI
from src.modules.free.auth.oauth.oauth import create_router

app = FastAPI()
app.include_router(create_router(), prefix="/oauth")
```

Implement the callback handler to validate state, exchange the authorisation code, and emit a
session for the authenticated user.

## 4. NestJS Integration

The NestJS artefacts mirror the Python runtime. Wire `OauthService` into your controllers and use
the generated DTOs to keep parameter names aligned across languages.

## 5. Testing

A repository level smoke suite lives under `tests/modules/free_auth_oauth`. Run it after customising
provider settings:

```bash
poetry run pytest tests/modules/free_auth_oauth -q
```

Extend the suite with application specific flows to validate provider callbacks and token exchange.
