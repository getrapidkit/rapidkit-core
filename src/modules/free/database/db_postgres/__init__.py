"""Runtime package for the PostgreSQL Database (db_postgres) module.

This module provides production-ready PostgreSQL integration with:
- Async/sync SQLAlchemy engines
- Connection pooling with configurable settings
- Transaction management with context managers
- Health check utilities
- FastAPI dependency injection support

Example:
    >>> from modules.free.database.db_postgres import get_module_info
    >>> info = get_module_info()
    >>> print(info['version'])
    1.0.4
"""

from __future__ import annotations

from typing import Any, Dict

__version__ = "1.0.4"
__all__ = ["DatabasePostgres", "get_module_info"]


def get_module_info() -> Dict[str, Any]:
    """
    Return module metadata and status information.

    Returns:
        Dictionary containing module version, status, and capabilities
    """
    return {
        "name": "db_postgres",
        "display_name": "PostgreSQL Database",
        "version": __version__,
        "status": "active",
        "tier": "free",
        "capabilities": [
            "async_engine",
            "sync_engine",
            "connection_pooling",
            "transaction_management",
            "health_checks",
            "dependency_injection",
        ],
        "frameworks": ["fastapi", "nestjs"],
        "python_version": ">=3.10,<4.0",
        "postgresql_version": ">=12.0",
    }


class DatabasePostgres:
    """
    PostgreSQL database module runtime interface.

    This class serves as a namespace for module-level operations and provides
    access to module metadata, configuration, and utilities.
    """

    @staticmethod
    def get_version() -> str:
        """Return module version."""
        return __version__

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """Return complete module information."""
        return get_module_info()
