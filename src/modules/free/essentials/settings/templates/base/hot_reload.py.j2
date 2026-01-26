import time
from contextlib import suppress
from typing import Any


def start_hot_reload(settings: Any, interval: int | None = None) -> None:
    """
    Naive polling-based hot reloader.
    In production, consider file watchers (watchdog) and signal-based reloads.
    """
    try:
        # Default to model value if not given
        refresh_interval = float(interval or getattr(settings, "CONFIG_REFRESH_INTERVAL", 60) or 60)
        while True:
            time.sleep(refresh_interval)
            with suppress(Exception):  # noqa: BLE001 - swallow to keep background thread alive
                settings.refresh()
    except Exception:  # noqa: BLE001
        pass


__all__ = ["start_hot_reload"]
