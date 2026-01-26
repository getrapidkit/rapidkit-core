# Migration

Guidance for upgrading existing projects to the 1.0.0 Celery module.

## From Scaffold (\<=0.1.0) to 1.0.0

- Regenerate the module to pick up the new runtime, FastAPI wrapper, and NestJS service.
- Update imports from `src/modules/free/tasks/celery/celery.py` to `rapidkit.runtime.tasks.celery`.
- Replace environment variables:
  - `CELERY_BROKER_URL` → `RAPIDKIT_CELERY_BROKER_URL`
  - `CELERY_RESULT_BACKEND` → `RAPIDKIT_CELERY_RESULT_BACKEND`
- Ensure Celery dependencies (`celery[redis]`, `redis`) are listed in project requirements.
- Merge the refreshed `.env` snippet to capture new fields like `RAPIDKIT_CELERY_AUTODISCOVER`.

## Enabling Beat Schedules

- Move schedule declarations into `defaults.settings.beat_schedule` or environment overrides.
- When migrating existing schedule dictionaries, add the `task` key explicitly per entry.

## NestJS Consumers

- Replace custom `celery-node` adapters with the generated `CeleryService`.
- Provide configuration via the exported `CELERY_CONFIG_TOKEN` and rely on `createCeleryHealthCheck`
  for Terminus probes.

## Testing Checklist Post-Upgrade

- Run module tests: `poetry run pytest tests/modules/free/tasks/celery -q`
- Exercise worker startup with new configuration: `celery -A apps.workers worker -l info`
- Validate FastAPI and NestJS health endpoints return expected broker metadata.
