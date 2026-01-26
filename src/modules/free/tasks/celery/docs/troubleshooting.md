# Troubleshooting

Common issues and resolutions when operating the Celery module.

## Cannot Connect to Broker

- **Symptom:** Celery raises `OperationalError: Error 111 connecting to localhost:6379`.
- **Fix:**
  - Verify `RAPIDKIT_CELERY_BROKER_URL` and ensure the broker is reachable.
  - If using TLS, ensure the URL includes the correct scheme and port.
  - Test connectivity with `redis-cli` or broker-specific CLI.

## Missing `celery` Package

- **Symptom:** `ModuleNotFoundError: No module named 'celery'`.
- **Fix:** Install dependencies with `pip install "celery[redis]" redis`. Re-run the worker after
  installation.

## Beat Schedule Not Triggering

- **Symptom:** Periodic tasks never execute.
- **Fix:**
  - Ensure each schedule entry defines both `task` and `schedule` keys.
  - For interval schedules, confirm `celery[schedule]` extras are installed if using crontab.
  - Start the beat process (`celery -A app beat`) or enable beat in worker command.

## FastAPI Dependency Raises RuntimeError

- **Symptom:** `RapidKit vendor payload ... not found` error.
- **Fix:**
  - Run `rapidkit modules install celery` to regenerate vendor payloads.
  - Confirm `.rapidkit/vendor/celery/<version>` exists within the project.

## NestJS Celery Client Rejections

- **Symptom:** `Failed to initialise Celery client` warning in NestJS logs.
- **Fix:**
  - Confirm `celery-node` is installed and accessible.
  - Ensure `brokerUrl` and `resultBackend` contain protocols (`redis://`).
  - Validate Redis credentials if authentication is required.

## Worker Memory Growth

- **Symptom:** Worker processes consume increasing memory.
- **Fix:**
  - Set `worker_max_tasks_per_child` to recycle workers periodically.
  - Investigate task payload size; consider streaming large results instead of returning them
    directly.
