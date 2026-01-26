# Advanced

This section outlines advanced Celery patterns supported by the RapidKit module.

## Custom Task Routing

- Extend `task_routes` in configuration to direct workloads to dedicated queues:
  ```yaml
  defaults:
  	settings:
  		task_routes:
  			"apps.workers.tasks.email": {queue: emails}
  			"apps.workers.tasks.reports": {queue: reporting}
  ```
- Update environment snippet `RAPIDKIT_CELERY_DEFAULT_QUEUE` to match fallback queues used in
  production.

## Beat Schedule with Interval Helpers

- Define schedules using interval metadata without requiring the optional `celery[schedule]` extras:
  ```yaml
  beat_schedule:
  	heartbeat:
  		task: apps.workers.tasks.heartbeat
  		schedule:
  			type: interval
  			every: 30
  			period: seconds
  ```
- When `celery[schedule]` is installed, the runtime converts the interval definition into a proper
  `schedule` object automatically.

## Enterprise Overrides

- Implement `CeleryOverrides.mutate_config` to inject organisation-specific queues or middleware:
  ```python
  class CustomCeleryOverrides(CeleryOverrides):
      def mutate_config(self, factory):
          config = factory()
          config.config_overrides["worker_hijack_root_logger"] = False
          return config
  ```
- Use `post_create` to register signals or monitoring hooks on the Celery app instance.

## Observability & Tracing

- Wrap task registration decorator to attach OpenTelemetry spans before dispatch.
- Hook into FastAPI/NestJS health endpoints to expose broker connectivity metrics.
- Leverage `CeleryTaskRegistry.list_task_names()` to feed dashboards with dynamic task inventories.

## Scaling Considerations

- Tune `worker_max_tasks_per_child` to mitigate memory leaks in long-running workers.
- Configure `result_expires` to manage backend storage utilization.
- For high throughput, deploy separate Celery instances per capability (email, notifications,
  billing) and use module overrides to align config.
