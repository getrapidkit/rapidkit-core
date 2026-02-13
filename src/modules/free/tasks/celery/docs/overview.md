# Celery Task Queue Module Overview

The Celery module provides distributed task queue orchestration with Redis broker support, scheduled
tasks (beat), and framework adapters for FastAPI and NestJS applications.

## Key Capabilities

- **Async task execution** – Offload long-running operations to background workers with result
  tracking.
- **Scheduled tasks** – Cron-based and interval-based task scheduling with Celery Beat integration.
- **Multiple queues** – Route tasks to specialized workers with priority and routing controls.
- **Result backends** – Store task results in Redis for status tracking and retrieval.
- **Health monitoring** – `/celery/status` endpoint reports broker connectivity and worker status.
- **Framework adapters** – FastAPI dependency injection and NestJS service wrapper with
  `celery-node`.

## Module Components

- **Celery App**: Core task queue runtime with broker/backend configuration
- **Task Decorators**: Define async tasks with retry and routing policies
- **Beat Scheduler**: Cron and interval scheduling for periodic tasks
- **Health Checks**: Broker and worker connectivity monitoring
- **Framework Adapters**: FastAPI routers and NestJS services

## Architecture

```
┌──────────────────────┐
│  Application         │
│  (FastAPI/NestJS)    │
└──────────────────────┘
         │
    ┌────────────────────┐
    │  Celery Client     │ ← Task submission
    └────────────────────┘
         │
    ┌────────────────────┐
    │  Redis Broker      │ ← Message queue
    └────────────────────┘
         │
    ┌────────────────────┐
    │  Celery Workers    │ ← Task execution
    └────────────────────┘
```

## Quick Start

### Define Tasks

```python
from rapidkit.runtime.tasks.celery import create_celery_app

celery_app = create_celery_app()


@celery_app.task
def send_email(to: str, subject: str, body: str):
    # Send email logic
    return {"status": "sent", "to": to}


@celery_app.task
def process_upload(file_id: str):
    # Process uploaded file
    return {"file_id": file_id, "processed": True}
```

### FastAPI Integration

```python
from fastapi import FastAPI, Depends
from src.modules.free.tasks.celery.celery import (
    get_celery_app_dependency,
    create_router,
)

app = FastAPI()
app.include_router(create_router())


@app.post("/tasks/email")
async def queue_email(
    to: str, subject: str, celery_app=Depends(get_celery_app_dependency)
):
    task = celery_app.send_task("send_email", args=[to, subject, "Welcome!"])
    return {"task_id": task.id, "status": "queued"}
```

### NestJS Integration

```typescript
import { Injectable } from '@nestjs/common';
import { CeleryService } from './celery/celery.service';

@Injectable()
export class TaskService {
  constructor(private celery: CeleryService) {}

  async queueEmail(to: string, subject: string) {
    const taskId = await this.celery.sendTask('send_email', [to, subject]);
    return { taskId, status: 'queued' };
  }
}
```

## Configuration

Environment variables:

```bash
RAPIDKIT_CELERY_BROKER_URL=redis://localhost:6379/0
RAPIDKIT_CELERY_RESULT_BACKEND=redis://localhost:6379/1
RAPIDKIT_CELERY_DEFAULT_QUEUE=default
RAPIDKIT_CELERY_ENABLE_UTC=true
RAPIDKIT_CELERY_TIMEZONE=UTC
RAPIDKIT_CELERY_IMPORTS=apps.workers.tasks
RAPIDKIT_CELERY_AUTODISCOVER=apps.workers
```

## Scheduled Tasks

### Cron Schedule

```python
from rapidkit.runtime.tasks.celery import CeleryAppConfig

config = CeleryAppConfig.from_mapping(
    {
        "beat_schedule": {
            "nightly_cleanup": {
                "task": "apps.workers.tasks.cleanup",
                "schedule": {"type": "crontab", "hour": 1, "minute": 0},
            }
        }
    }
)
```

### Interval Schedule

```python
config = CeleryAppConfig.from_mapping(
    {
        "beat_schedule": {
            "health_check": {
                "task": "apps.workers.tasks.health_check",
                "schedule": {"type": "interval", "seconds": 300},  # Every 5 minutes
            }
        }
    }
)
```

## Task Routing

Route tasks to specific queues:

```python
@celery_app.task(queue="high_priority")
def urgent_task():
    pass


@celery_app.task(queue="background")
def batch_process():
    pass


# Start workers for specific queues
# celery -A worker worker --queue=high_priority
```

## Retry Logic

Configure automatic retries:

```python
@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def flaky_task(self, data):
    try:
        # Task logic
        pass
    except Exception as exc:
        raise self.retry(exc=exc)
```

## Worker Management

Start workers:

```bash
# Single worker
celery -A worker worker --loglevel=INFO

# Multiple workers with concurrency
celery -A worker worker --concurrency=4

# Specific queue
celery -A worker worker --queue=high_priority

# Beat scheduler
celery -A worker beat --loglevel=INFO
```

## Result Tracking

Check task status:

```python
from celery.result import AsyncResult

task = celery_app.send_task("process_upload", args=["file123"])
result = AsyncResult(task.id, app=celery_app)

print(result.state)  # PENDING, STARTED, SUCCESS, FAILURE
print(result.result)  # Task return value
```

## Health Monitoring

Health endpoint reports:

- Broker connectivity
- Active workers count
- Queue depths
- Recent task statistics

```json
{
  "status": "healthy",
  "module": "celery",
  "broker": {
    "connected": true,
    "url": "redis://localhost:6379/0"
  },
  "workers": {
    "active": 4,
    "queues": ["default", "high_priority"]
  },
  "tasks": {
    "completed_last_hour": 1234,
    "failed_last_hour": 2
  }
}
```

Access at `/celery/status`.

## Supported Frameworks

- **FastAPI**: Full async support with lifespan management
- **NestJS**: Service wrapper using `celery-node`
- **Custom**: Direct Celery app instantiation

## Performance Features

- **Worker concurrency**: Multiple processes or threads per worker
- **Prefetch multiplier**: Control task batching per worker
- **Result compression**: Reduce result backend storage
- **Task prioritization**: Route urgent tasks to dedicated queues

## Security Features

- **Broker authentication**: Redis password protection
- **Result encryption**: Encrypt sensitive task results
- **Task signing**: Verify task authenticity
- **Network isolation**: Run workers in separate network segments

## Getting Help

- **Overview**: This document
- **Usage Guide**: `docs/usage.md`

For issues and questions, visit our
[GitHub repository](https://github.com/getrapidkit/rapidkit-core).
