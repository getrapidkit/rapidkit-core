"""Runtime primitives for orchestrating Celery task processing."""

from __future__ import annotations

import importlib
import os
from dataclasses import dataclass, field
from datetime import timedelta
from functools import lru_cache
from typing import Any, Callable, Mapping, MutableMapping, Optional, Sequence, cast

Celery: Any
crontab: Any | None
celery_schedule: Any | None

try:  # Optional dependency
    celery_module = importlib.import_module("celery")
    schedules_module = importlib.import_module("celery.schedules")
except ImportError:  # pragma: no cover - optional dependency not installed
    Celery = None
    crontab = None
    celery_schedule = None
else:
    Celery = getattr(celery_module, "Celery", None)
    crontab = getattr(schedules_module, "crontab", None)
    celery_schedule = getattr(schedules_module, "schedule", None)


DEFAULT_ENV_PREFIX = "RAPIDKIT_CELERY_"


class CeleryRuntimeError(RuntimeError):
    """Raised when Celery runtime operations fail."""


@dataclass(slots=True)
class CelerySchedule:
    """Represents a Celery beat schedule entry."""

    task: str
    schedule: Any
    args: Sequence[Any] = field(default_factory=tuple)
    kwargs: Mapping[str, Any] = field(default_factory=dict)
    options: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "CelerySchedule":
        task = payload.get("task")
        if not isinstance(task, str) or not task:
            raise ValueError("Celery schedule payload requires a non-empty 'task'")
        schedule = payload.get("schedule")
        if schedule is None:
            raise ValueError("Celery schedule payload missing 'schedule'")
        derived = _coerce_schedule(schedule)
        return cls(
            task=task,
            schedule=derived,
            args=tuple(payload.get("args", ()) or ()),
            kwargs=dict(payload.get("kwargs", {}) or {}),
            options=dict(payload.get("options", {}) or {}),
        )


@dataclass(slots=True)
class CelerySettings:
    """Encapsulates Celery configuration options."""

    broker_url: str = "redis://localhost:6379/0"
    result_backend: Optional[str] = "redis://localhost:6379/1"
    timezone: str = "UTC"
    enable_utc: bool = True
    task_default_queue: str = "default"
    task_routes: MutableMapping[str, Any] = field(default_factory=dict)
    task_annotations: MutableMapping[str, Any] = field(default_factory=dict)
    imports: Sequence[str] = field(default_factory=tuple)
    include: Sequence[str] = field(default_factory=tuple)
    beat_schedule: MutableMapping[str, CelerySchedule] = field(default_factory=dict)
    worker_max_tasks_per_child: Optional[int] = None
    result_expires: Optional[int] = 3600

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "CelerySettings":
        defaults = cls()
        beat_payload = payload.get("beat_schedule", {}) or {}
        schedule_map: MutableMapping[str, CelerySchedule] = {}
        for name, entry in beat_payload.items():
            if not isinstance(entry, Mapping):
                raise ValueError("beat_schedule entries must be mappings")
            schedule_map[str(name)] = CelerySchedule.from_mapping(entry)
        return cls(
            broker_url=str(payload.get("broker_url", defaults.broker_url)),
            result_backend=_maybe(payload.get("result_backend"), default=defaults.result_backend),
            timezone=str(payload.get("timezone", defaults.timezone)),
            enable_utc=bool(payload.get("enable_utc", defaults.enable_utc)),
            task_default_queue=str(payload.get("task_default_queue", defaults.task_default_queue)),
            task_routes=dict(payload.get("task_routes", {}) or {}),
            task_annotations=dict(payload.get("task_annotations", {}) or {}),
            imports=tuple(payload.get("imports", ()) or ()),
            include=tuple(payload.get("include", ()) or ()),
            beat_schedule=schedule_map,
            worker_max_tasks_per_child=_maybe(payload.get("worker_max_tasks_per_child")),
            result_expires=_maybe(payload.get("result_expires"), default=defaults.result_expires),
        )


@dataclass(slots=True)
class CeleryAppConfig:
    """High level configuration used to build Celery applications."""

    name: str = "rapidkit"
    settings: CelerySettings = field(default_factory=CelerySettings)
    namespace: str = "CELERY"
    autodiscover: Sequence[str] = field(default_factory=tuple)
    config_overrides: MutableMapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "CeleryAppConfig":
        defaults = cls()
        settings_payload = payload.get("settings", {}) or {}
        return cls(
            name=str(payload.get("name", defaults.name)),
            settings=CelerySettings.from_mapping(settings_payload),
            namespace=str(payload.get("namespace", defaults.namespace)),
            autodiscover=tuple(payload.get("autodiscover", ()) or ()),
            config_overrides=dict(payload.get("config_overrides", {}) or {}),
        )


class CeleryTaskRegistry:
    """Utility used to register and introspect Celery tasks."""

    def __init__(self, app: Any) -> None:
        self._app = app

    def task(
        self, *decorator_args: Any, **decorator_kwargs: Any
    ) -> Callable[[Callable[..., Any]], Any]:
        if Celery is None:
            raise CeleryRuntimeError(
                "Celery is required to register tasks. Install it via 'pip install celery[redis]'."
            )
        return cast(
            Callable[[Callable[..., Any]], Any],
            self._app.task(*decorator_args, **decorator_kwargs),
        )

    def list_task_names(self) -> Sequence[str]:
        registered = getattr(self._app, "tasks", {})
        return tuple(sorted(name for name in registered))


def _maybe(value: Any, *, default: Any = None) -> Any:
    return default if value in (None, "") else value


def _coerce_schedule(schedule: Any) -> Any:
    if isinstance(schedule, Mapping):
        schedule_type = str(schedule.get("type", "")).lower()
        if schedule_type == "crontab":
            if crontab is None:
                raise CeleryRuntimeError("celery[schedule] extras required for crontab support.")
            return crontab(
                minute=schedule.get("minute", "*"),
                hour=schedule.get("hour", "*"),
                day_of_week=schedule.get("day_of_week", "*"),
                day_of_month=schedule.get("day_of_month", "*"),
                month_of_year=schedule.get("month_of_year", "*"),
            )
        if schedule_type == "interval":
            every = schedule.get("every")
            period = str(schedule.get("period", "seconds")).lower()
            if every is None:
                raise ValueError("Interval schedules require 'every' and 'period'")
            if celery_schedule is None:
                return {"every": every, "period": period}
            delta_kwargs: MutableMapping[str, Any] = {}
            if period not in {"seconds", "minutes", "hours", "days"}:
                raise ValueError("Interval period must be one of seconds, minutes, hours, or days")
            delta_kwargs[period] = every
            return celery_schedule(run_every=timedelta(**delta_kwargs))
    return schedule


def create_celery_app(config: CeleryAppConfig) -> Any:
    if Celery is None:
        raise CeleryRuntimeError(
            "Celery is not installed. Install via 'pip install celery[redis]'."
        )
    app = Celery(
        config.name, broker=config.settings.broker_url, backend=config.settings.result_backend
    )
    app.conf.update(
        enable_utc=config.settings.enable_utc,
        timezone=config.settings.timezone,
        task_default_queue=config.settings.task_default_queue,
        task_routes=config.settings.task_routes,
        task_annotations=config.settings.task_annotations,
        imports=list(config.settings.imports),
        include=list(config.settings.include),
        result_expires=config.settings.result_expires,
        worker_max_tasks_per_child=config.settings.worker_max_tasks_per_child,
        beat_schedule={
            name: _serialise_schedule(entry)
            for name, entry in config.settings.beat_schedule.items()
        },
        **config.config_overrides,
    )
    if config.autodiscover:
        app.autodiscover_tasks(config.autodiscover, force=True)
    return app


def _serialise_schedule(entry: CelerySchedule) -> Mapping[str, Any]:
    payload: MutableMapping[str, Any] = {
        "task": entry.task,
        "schedule": entry.schedule,
        "args": list(entry.args),
        "kwargs": dict(entry.kwargs),
        "options": dict(entry.options),
    }
    return payload


@lru_cache(maxsize=1)
def _get_default_celery_app() -> Any:
    return create_celery_app(CeleryAppConfig())


def get_celery_app(config: CeleryAppConfig | None = None) -> Any:
    if config is None:
        return _get_default_celery_app()
    return create_celery_app(config)


def load_config_from_env(
    prefix: str = DEFAULT_ENV_PREFIX, env: Mapping[str, str] | None = None
) -> CeleryAppConfig:
    source = env or os.environ
    settings_payload: MutableMapping[str, Any] = {
        "broker_url": source.get(f"{prefix}BROKER_URL"),
        "result_backend": source.get(f"{prefix}RESULT_BACKEND"),
        "timezone": source.get(f"{prefix}TIMEZONE"),
        "enable_utc": _flag(source.get(f"{prefix}ENABLE_UTC")),
        "task_default_queue": source.get(f"{prefix}DEFAULT_QUEUE"),
    }
    name = source.get(f"{prefix}APP_NAME", "rapidkit")
    autodiscover = _split_list(source.get(f"{prefix}AUTODISCOVER"))
    include = _split_list(source.get(f"{prefix}INCLUDE"))
    imports = _split_list(source.get(f"{prefix}IMPORTS"))
    settings_payload["include"] = include
    settings_payload["imports"] = imports
    settings = CelerySettings.from_mapping(
        {k: v for k, v in settings_payload.items() if v not in (None, "")}
    )
    return CeleryAppConfig(
        name=name,
        settings=settings,
        autodiscover=tuple(autodiscover),
    )


def _flag(value: Optional[str]) -> Optional[bool]:
    if value is None:
        return None
    return value.lower() in {"1", "true", "yes", "on"}


def _split_list(value: Optional[str]) -> Sequence[str]:
    if not value:
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())
