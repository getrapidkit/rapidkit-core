# Logging Module Usage Guide

The RapidKit logging module provides a structured logging runtime with queue-based handlers,
correlation context propagation, and framework adapters for FastAPI and NestJS projects. This guide
walks through the steps required to generate the artefacts, wire them into an application, and
customise behaviour safely.

## 1. Generate Artefacts

```bash
rapidkit add module logging
rapidkit modules lock --overwrite
```

The generator publishes vendor sources into `.rapidkit/vendor/logging/<version>` and renders the
selected framework variant into your project. To re-render manually:

```bash
poetry run python -m src.modules.free.essentials.logging.generate fastapi .
poetry run python -m src.modules.free.essentials.logging.generate nestjs ./nestjs
```

## 2. Configure Environment Defaults

| Variable                           | Description                                                     |
| ---------------------------------- | --------------------------------------------------------------- |
| `LOG_LEVEL`                        | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |
| `LOG_FORMAT`                       | Output format (`json`, `text`, `colored`)                       |
| `LOG_SINKS`                        | Sequence of sinks (`stderr`, `file`, `syslog`)                  |
| `LOG_FILE_PATH`                    | Path used by the file sink                                      |
| `LOG_ASYNC_QUEUE`                  | Enable asynchronous queue handlers                              |
| `LOG_SAMPLING_RATE`                | Float between 0 and 1 controlling sampling                      |
| `LOG_ENABLE_REDACTION`             | Toggle secret redaction filters                                 |
| `OTEL_BRIDGE_ENABLED`              | Enable the OpenTelemetry bridge handler                         |
| `METRICS_BRIDGE_ENABLED`           | Enable the metrics bridge handler                               |
| `RAPIDKIT_LOGGING_REQUEST_CONTEXT` | Enable or disable request context propagation                   |

Defaults can be overridden globally through the new override contracts (see `overrides.py`) or per
environment by adjusting the variables listed above.

## 3. FastAPI Integration

```python
from src.modules.free.essentials.logging.logging import (
    get_logger,
    RequestContextMiddleware,
)
from fastapi import FastAPI

app = FastAPI()
app.add_middleware(RequestContextMiddleware)
logger = get_logger(__name__)


@app.get("/health")
async def health() -> dict[str, str]:
    logger.info("health check")
    return {"status": "ok"}
```

The middleware injects `request_id` and `user_id` context, making correlation data available across
handlers.

## 4. NestJS Integration

```typescript
import { LoggingModule } from './modules/free/essentials/logging';

@Module({
  imports: [LoggingModule.register()],
})
export class AppModule {}
```

Generated helpers provide configuration, validation, and index exports so NestJS consumers can
declare the module with minimal boilerplate.

## 5. Runtime Overrides

Set any of the following environment variables _before_ invoking the generator to tweak defaults:

- `RAPIDKIT_LOGGING_FORCE_LEVEL`
- `RAPIDKIT_LOGGING_FORCE_FORMAT`
- `RAPIDKIT_LOGGING_FORCE_SINKS`
- `RAPIDKIT_LOGGING_FORCE_ASYNC_QUEUE`
- `RAPIDKIT_LOGGING_FORCE_REDACTION`
- `RAPIDKIT_LOGGING_FORCE_OTEL`
- `RAPIDKIT_LOGGING_FORCE_METRICS`
- `RAPIDKIT_LOGGING_EXTRA_SNIPPET` / `RAPIDKIT_LOGGING_EXTRA_SNIPPET_DEST`

Refer to `docs/troubleshooting.md` for debugging tips.
