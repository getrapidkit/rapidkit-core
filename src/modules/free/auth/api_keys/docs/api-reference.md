# API Reference

List public classes, methods, and response models exposed by the generated module.

## Runtime Classes

- `ApiKeys`: runtime facade implementing issue/verify/revoke.
- `ApiKeysConfig`: configuration model (defaults generated from `config/api_keys.yaml`).
- `ApiKeysTelemetry`: lightweight counters and timings used for monitoring.

## FastAPI adapter

- `build_router(prefix=...)`: returns an `APIRouter` exposing `/metadata` and `/health` plus
  issuance endpoints.
- `get_runtime(config=...)`: helper to construct the runtime from a mapping or config model.
