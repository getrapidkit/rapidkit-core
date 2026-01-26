# API Reference

This section summarises the public classes exported by the generated module templates. Names
referenced here map directly to the files rendered in downstream projects.

## Python Runtime (`src/modules/free/security/security_headers/security_headers.py`)

### `SecurityHeadersConfig`

Dataclass mirroring the default policy. Notable fields:

- `enabled: bool` – Master toggle; when `False` no headers are applied.
- `strict_transport_security_max_age: int` – Seconds appended to the `Strict-Transport-Security`
  header.
- `permissions_policy: dict[str, str | Sequence[str] | None]` – Directive/value map rendered into
  `Permissions-Policy`.
- `additional_headers: dict[str, str]` – Extra headers merged onto the computed payload.

### `SecurityHeaders`

| Method                           | Returns             | Description                                                                        |
| -------------------------------- | ------------------- | ---------------------------------------------------------------------------------- |
| `headers(refresh: bool = False)` | `dict[str, str]`    | Construct the active header map. Set `refresh=True` after mutating the config.     |
| `apply(target)`                  | `dict[str, str]`    | Mutate a response header mapping in-place, returning the applied values.           |
| `metadata()`                     | `dict[str, object]` | Diagnostic payload containing module title, enablement state, and config snapshot. |
| `health_check()`                 | `dict[str, object]` | Calls into the health helpers to provide metrics for monitoring.                   |

## FastAPI Adapter (`src/modules/free/security/security_headers/security_headers.py`)

- `SecurityHeadersSettings` – Pydantic model validated before instantiating the runtime.
- `SecurityHeadersMiddleware` – Starlette middleware that applies headers to outbound responses.
- `register_fastapi(app, config=None)` – Adds middleware, persists state on `app.state`, and mounts
  the generated router.
- `get_runtime()` – Accessor for the shared singleton runtime (useful within routers or dependency
  overrides).

## NestJS Adapter (`src/modules/free/security/security_headers/security-headers/*.ts`)

- `SecurityHeadersService` – Injectable service exposing `apply(response)`, `getHeaders()`, and
  `health()` functions.
- `SecurityHeadersModule.register(options?: Partial<SecurityHeadersOptions>)` – Dynamic module
  helper that injects custom configuration.
- `SecurityHeadersController` – Exposes `/security-headers/health` and `/security-headers/headers`
  endpoints by default.

## Health Helpers (`src/health/security_headers.py`)

- `evaluate_completeness(config, headers)` – Returns metrics indicating missing recommended headers.
- `build_health_payload(module, status, headers, metrics)` – Shapes the health payload consumed by
  both FastAPI and NestJS adapters.
