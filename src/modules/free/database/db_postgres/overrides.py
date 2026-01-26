"""Runtime override contracts for the db_postgres module.

This module demonstrates how to layer safe, upgrade-friendly customisations on
top of the generated PostgreSQL database integration. The overrides latch onto
well-defined extension points and can be toggled through environment variables,
keeping the core implementation untouched while giving operators room to adapt
behaviour.

The overrides are registered via ``core.services.override_contracts`` and become
active once applied in the FastAPI variant. Behavioural knobs include:

- RAPIDKIT_DB_POSTGRES_POOL_PRE_PING: Enable connection health checks before checkout
- RAPIDKIT_DB_POSTGRES_ECHO_POOL: Log all connection pool events
- RAPIDKIT_DB_POSTGRES_STATEMENT_TIMEOUT: Set statement timeout in seconds
- RAPIDKIT_DB_POSTGRES_SLOW_QUERY_THRESHOLD: Log queries slower than N seconds
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict

from core.services.override_contracts import override_method

logger = logging.getLogger("rapidkit.modules.db_postgres.overrides")


def _get_bool_env(key: str, default: bool = False) -> bool:
    """Parse boolean environment variable."""
    value = os.getenv(key, "").lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    return default


def _get_int_env(key: str, default: int = 0) -> int:
    """Parse integer environment variable."""
    try:
        return int(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


def _get_float_env(key: str, default: float = 0.0) -> float:
    """Parse float environment variable."""
    try:
        return float(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


@override_method("get_engine_config")
def _enhance_engine_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Enhance SQLAlchemy engine configuration with runtime overrides."""

    enhanced = config.copy()

    # Enable connection health checks
    if _get_bool_env("RAPIDKIT_DB_POSTGRES_POOL_PRE_PING"):
        enhanced["pool_pre_ping"] = True
        logger.info("Enabled pool_pre_ping via RAPIDKIT_DB_POSTGRES_POOL_PRE_PING")

    # Enable pool event logging
    if _get_bool_env("RAPIDKIT_DB_POSTGRES_ECHO_POOL"):
        enhanced["echo_pool"] = True
        logger.info("Enabled echo_pool via RAPIDKIT_DB_POSTGRES_ECHO_POOL")

    # Set statement timeout
    statement_timeout = _get_int_env("RAPIDKIT_DB_POSTGRES_STATEMENT_TIMEOUT")
    if statement_timeout > 0:
        if "connect_args" not in enhanced:
            enhanced["connect_args"] = {}
        enhanced["connect_args"]["options"] = f"-c statement_timeout={statement_timeout}s"
        logger.info(
            "Set statement_timeout to %ds via RAPIDKIT_DB_POSTGRES_STATEMENT_TIMEOUT",
            statement_timeout,
        )

    return enhanced


@override_method("check_postgres_connection")
async def _enhanced_health_check() -> None:
    """Add custom health check logging and metrics."""

    original = globals().get("_original_check_postgres_connection")
    if callable(original):
        await original()

    # Log health check if enabled
    if _get_bool_env("RAPIDKIT_DB_POSTGRES_LOG_HEALTH_CHECKS"):
        logger.debug("PostgreSQL health check passed")


@override_method("get_postgres_db")
async def _track_slow_queries(session: Any) -> Any:
    """Track and log slow database queries."""

    import time

    threshold = _get_float_env("RAPIDKIT_DB_POSTGRES_SLOW_QUERY_THRESHOLD", 0.0)
    if threshold <= 0:
        yield session
        return

    start_time = time.time()
    try:
        yield session
    finally:
        duration = time.time() - start_time
        if duration > threshold:
            logger.warning(
                "Slow database session detected: %.2fs (threshold: %.2fs)", duration, threshold
            )


class DatabasePostgresOverrides:
    """
    Override contracts for db_postgres module.

    Environment Variables:
        RAPIDKIT_DB_POSTGRES_POOL_PRE_PING: Enable connection health checks
        RAPIDKIT_DB_POSTGRES_ECHO_POOL: Log connection pool events
        RAPIDKIT_DB_POSTGRES_STATEMENT_TIMEOUT: Statement timeout in seconds
        RAPIDKIT_DB_POSTGRES_SLOW_QUERY_THRESHOLD: Log queries slower than N seconds
        RAPIDKIT_DB_POSTGRES_LOG_HEALTH_CHECKS: Log health check executions
    """

    @staticmethod
    def apply_overrides() -> None:
        """Apply all registered overrides."""
        logger.info("Database PostgreSQL overrides registered")
