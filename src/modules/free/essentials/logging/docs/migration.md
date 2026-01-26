# Logging Module Migration Guide

This guide helps teams upgrade from legacy logging scaffolds to the unified RapidKit logging module.

## 1. Prepare the Project

1. Remove bespoke logging utilities and retain only the configuration entry points that integrate
   with application code.
1. Ensure the project is on Python 3.10+ (FastAPI) or Node 16+ (NestJS) and is using the unified
   settings module if request context propagation is required.

## 2. Generate the New Artefacts

```bash
rapidkit add module logging --profile fastapi.standard
rapidkit modules lock --overwrite
```

Repeat for the NestJS profile when applicable. Commit the new vendor snapshot under
`.rapidkit/vendor/logging/<version>`.

## 3. Replace Imports

- Update Python imports to use `src.modules.free.essentials.logging.logging.get_logger` and
  `RequestContextMiddleware`.
- Replace NestJS imports with the generated exports under `src/modules/free/essentials/logging`.

## 4. Align Environment Variables

Map existing environment variables to the new schema (see `config/base.yaml`). The most common
mappings are:

| Legacy Variable         | Replacement       |
| ----------------------- | ----------------- |
| `APP_LOG_LEVEL`         | `LOG_LEVEL`       |
| `APP_LOG_FORMAT`        | `LOG_FORMAT`      |
| `APP_LOG_STRUCTURED`    | `LOG_FORMAT=json` |
| `APP_LOG_DISABLE_QUEUE` | `LOG_ASYNC_QUEUE` |

## 5. Enable Overrides Gradually

If you relied on bespoke monkey patches, port them to the override contracts provided in
`overrides.py`. This keeps custom logic upgrade-safe and audit-friendly.

## 6. Validate

Run the testing checklist from the README and confirm that generated artefacts and vendor payloads
behave as expected. Remove the legacy logging code once parity is achieved.
