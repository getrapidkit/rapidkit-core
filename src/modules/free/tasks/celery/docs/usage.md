# Usage

This guide walks through configuring the RapidKit Celery module and wiring it into FastAPI and
NestJS applications.

## Prerequisites

- Python `>=3.10`
- Node.js `>=18`
- Redis or other Celery-compatible broker/result backend
- Required packages:
  - `pip install "celery[redis]" redis`
  - `npm install celery-node`

## Configure Environment

Merge the generated snippet or add these variables to your `.env`:

```bash
RAPIDKIT_CELERY_BROKER_URL=redis://localhost:6379/0
RAPIDKIT_CELERY_RESULT_BACKEND=redis://localhost:6379/1
RAPIDKIT_CELERY_DEFAULT_QUEUE=default
RAPIDKIT_CELERY_ENABLE_UTC=true
RAPIDKIT_CELERY_TIMEZONE=UTC
RAPIDKIT_CELERY_IMPORTS=apps.workers.tasks
RAPIDKIT_CELERY_AUTODISCOVER=apps.workers
```

You can override these defaults in `config/base.yaml` before generation to align with project
conventions.

## Python Runtime

```python
from rapidkit.runtime.tasks.celery import (
    CeleryAppConfig,
    CelerySettings,
    CelerySchedule,
    create_celery_app,
    load_config_from_env,
)

config = CeleryAppConfig.from_mapping(
    {
        "name": "worker",
        "settings": {
            "broker_url": "redis://localhost:6379/0",
            "imports": ["apps.workers.tasks"],
            "beat_schedule": {
                "nightly_cleanup": {
                    "task": "apps.workers.tasks.cleanup",
                    "schedule": {
                        "type": "crontab",
                        "hour": 1,
                        "minute": 0,
                    },
                }
            },
        },
    }
)

app = create_celery_app(config)


@app.task
def echo(message: str) -> str:
    return message


echo.apply_async(args=["hello"], countdown=10)
```

### Loading from Environment

```python
config = load_config_from_env()
celery_app = create_celery_app(config)
```

## FastAPI Integration

The generated FastAPI module exposes dependency helpers:

```python
from fastapi import Depends, FastAPI
from src.modules.free.tasks.celery.celery import (
    create_router,
    get_celery_app_dependency,
)

app = FastAPI()
app.include_router(create_router())


@app.post("/tasks/echo")
async def trigger_task(message: str, celery_app=Depends(get_celery_app_dependency)):
    celery_app.send_task("apps.workers.tasks.echo", args=[message])
    return {"status": "queued"}
```

Use `register_celery_lifespan(app, eager_load=True)` to warm the Celery client during startup if
desired.

## NestJS Integration

The NestJS variant provides a service wrapper using `celery-node`:

```typescript
import { Module } from '@nestjs/common';
import { CeleryService, CELERY_CONFIG_TOKEN } from './celery/celery.service';

@Module({
	providers: [
		CeleryService,
		{
			provide: CELERY_CONFIG_TOKEN,
			useValue: {
				enabled: true,
				connection: {
					brokerUrl: process.env.RAPIDKIT_CELERY_BROKER_URL,
					resultBackend: process.env.RAPIDKIT_CELERY_RESULT_BACKEND,
					defaultQueue: 'default',
				},
				defaultHeaders: {
					'X-App-Module': 'celery',
				},
			},
		},
	],
	exports: [CeleryService],
})
export class CeleryModule {}

// Usage inside a controller/service
await this.celeryService.sendTask('apps.workers.tasks.echo', ['hello world']);
```

## Worker Entrypoint Example

```python
from rapidkit.runtime.tasks.celery import load_config_from_env, create_celery_app

celery_app = create_celery_app(load_config_from_env())

if __name__ == "__main__":
    celery_app.worker_main(argv=["worker", "--loglevel=INFO"])
```

## Health Checks

- FastAPI router exposes `/celery/status` showing broker details.
- NestJS helper `createCeleryHealthCheck(service)` returns health summary for Terminus integration.
