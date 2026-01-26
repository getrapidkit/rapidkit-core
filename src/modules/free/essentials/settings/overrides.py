# pyright: reportMissingImports=false

"""Runtime override contracts for the settings module.

This module demonstrates how to layer safe, upgrade-friendly customisations on
top of the generated settings payload. The overrides latch onto well-defined
extension points and can be toggled through environment variables, keeping the
core implementation untouched while giving operators room to adapt behaviour.

The overrides are registered via ``core.services.override_contracts`` and become
active once ``apply_module_overrides(Settings, "settings")`` runs (the FastAPI
variant template calls this automatically). Behavioural knobs are summarised in
the module README.
"""

from __future__ import annotations

import importlib
import inspect
import logging
import os
from collections.abc import Iterable
from typing import Any, Tuple, cast

from core.services.override_contracts import override_method

logger = logging.getLogger("rapidkit.modules.settings.overrides")  # pylint: disable=E1101


def _split_env_list(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _coerce_iterable(value: Iterable[Any] | Tuple[Any, ...]) -> Tuple[Any, ...]:
    if isinstance(value, tuple):
        return value
    return tuple(value)


@override_method("Settings.settings_customise_sources")
def _append_extra_dotenv_sources(
    cls: type,
    settings_cls: type,
    init_settings: Any,
    env_settings: Any,
    dotenv_settings: Any,
    file_secret_settings: Any,
) -> Tuple[Any, ...]:
    """Allow operators to extend the dotenv search path dynamically."""

    original = getattr(cls, "_original_settings_customise_sources", None)
    if callable(original):
        sources = original(
            settings_cls,
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )
    else:
        sources = (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )

    # Ensure we always return a tuple for type checkers
    sources = _coerce_iterable(cast(Iterable[Any] | Tuple[Any, ...], sources))

    extra_dotenvs = _split_env_list(os.getenv("RAPIDKIT_SETTINGS_EXTRA_DOTENV"))
    if not extra_dotenvs:
        return _coerce_iterable(sources)

    try:
        module = importlib.import_module("pydantic_settings")
        DotEnvSettingsSource = cast(Any, module.DotEnvSettingsSource)
    except ImportError:  # pragma: no cover - optional dependency
        logger.warning(
            "Skipping RAPIDKIT_SETTINGS_EXTRA_DOTENV because pydantic_settings is missing. "
            "Install it via 'pip install pydantic-settings' to load custom dotenv files."
        )
        return _coerce_iterable(sources)
    except AttributeError:  # pragma: no cover - defensive
        logger.warning(
            "pydantic_settings module found but DotEnvSettingsSource is unavailable; "
            "skipping RAPIDKIT_SETTINGS_EXTRA_DOTENV"
        )
        return _coerce_iterable(sources)

    existing = _coerce_iterable(cast(Iterable[Any] | Tuple[Any, ...], sources))
    additional = tuple(
        DotEnvSettingsSource(settings_cls, env_file=str(path), case_sensitive=True)
        for path in extra_dotenvs
    )
    logger.info(
        "Attached %d additional dotenv source(s) via RAPIDKIT_SETTINGS_EXTRA_DOTENV",
        len(additional),
    )
    return (*existing, *additional)


@override_method("Settings.validate_production_settings")
def _relaxed_production_validation(self: Any) -> Any:
    """Optionally relax production guards for selected environments."""

    original = getattr(self, "_original_validate_production_settings", None)
    if callable(original):
        if inspect.ismethod(original):
            original()
        else:
            original(self)

    relaxed_envs = set(_split_env_list(os.getenv("RAPIDKIT_SETTINGS_RELAXED_ENVS")))
    allow_placeholder = os.getenv(
        "RAPIDKIT_SETTINGS_ALLOW_PLACEHOLDER_SECRET", "false"
    ).lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    if not relaxed_envs or not allow_placeholder or self.ENV not in relaxed_envs:
        return self

    placeholder = getattr(type(self), "SECRET_PLACEHOLDER", "changemechangemechangemechangeme")
    if placeholder == self.SECRET_KEY:
        logger.warning(
            "SECRET_KEY placeholder accepted for env '%s' due to override contract", self.ENV
        )
        logger.info("RAPIDKIT_SETTINGS_RELAXED_ENVS override active for env '%s'", self.ENV)
    return self


@override_method("Settings.refresh")
def _refresh_with_observability(self: Any) -> None:
    """Emit a structured log line whenever settings refresh is triggered."""

    original = getattr(self, "_original_refresh", None)
    if callable(original):
        if inspect.ismethod(original):
            original()
        else:
            original(self)
    else:  # pragma: no cover - defensive
        type(self).refresh(self)

    if os.getenv("RAPIDKIT_SETTINGS_LOG_REFRESH", "false").lower() not in {
        "1",
        "true",
        "yes",
        "on",
    }:
        return

    logger.info(
        "Settings refresh executed",
        extra={"env": self.ENV, "hot_reload": self.HOT_RELOAD_ENABLED},
    )
