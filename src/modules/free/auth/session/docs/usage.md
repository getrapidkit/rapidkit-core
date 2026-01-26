# Session Module Usage Guide

## 1. Install the Module

```bash
rapidkit add module session
rapidkit modules lock --overwrite
```

Runtime helpers are rendered into `src/modules/free/auth/session/session.py` and vendor code under
`.rapidkit/vendor/session/<version>`.

## 2. Issue Sessions

```python
from src.modules.free.auth.session.session import SessionRuntime, load_session_settings

runtime = SessionRuntime(
    load_session_settings({"secret_key": "super-secret", "session_ttl_seconds": 3600})
)
envelope = runtime.issue_session(user_id="user-123", payload={"roles": ["member"]})
token = envelope.token
```

Persist the token in an HTTP-only cookie or your preferred storage mechanism.

## 3. Validate Requests

```python
from fastapi import Depends, HTTPException

runtime = SessionRuntime(
    load_session_settings({"secret_key": settings.SESSION_SECRET_KEY})
)


def require_session(token: str = Depends(read_cookie)) -> dict[str, str]:
    try:
        session = runtime.verify_session_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return {"session_id": session.session_id, "user_id": session.user_id}
```

## 4. Rolling Expiration

Use refresh token rotation via `runtime.rotate_session(refresh_token)` to extend sessions.

## 5. Testing

Execute the repository tests whenever you change signing or TTL rules:

```bash
poetry run pytest tests/modules/free_auth_session -q
```
