"""Override contracts for the Celery module."""

from __future__ import annotations

from typing import Callable

from core.services.override_contracts import ConfigurableOverrideMixin


class CeleryOverrides(ConfigurableOverrideMixin):
    """Extend or customize Celery runtime behaviour in enterprise editions."""

    def mutate_config(self, factory: Callable[[], object]) -> object:
        """Hook to adjust the Celery configuration before the app is created."""

        return factory()

    def post_create(self, app: object) -> object:
        """Hook invoked after the Celery application is constructed."""

        return app
