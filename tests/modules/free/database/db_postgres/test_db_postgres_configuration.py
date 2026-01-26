"""Configuration sanity checks for Db Postgres."""

from __future__ import annotations

import yaml


def test_base_config_variables_defaults(module_root) -> None:
    config_path = module_root / "config/base.yaml"
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    variables = data.get("variables", {})

    database_url = variables.get("database_url", {})
    assert database_url.get("default", "").startswith("postgresql://")
    assert database_url.get("env_var") == "DATABASE_URL"

    pool_size = variables.get("db_pool_size", {})
    assert pool_size.get("default") == 10
    assert pool_size.get("env_var") == "DB_POOL_SIZE"

    pool_timeout = variables.get("db_pool_timeout", {})
    assert pool_timeout.get("default") == 30
    assert pool_timeout.get("env_var") == "DB_POOL_TIMEOUT"


def test_dependency_matrix_includes_drivers(module_config: dict[str, object]) -> None:
    dependencies = module_config.get("dependencies", {}).get("fastapi", [])  # type: ignore[assignment]
    names = {dep.get("name") for dep in dependencies if isinstance(dep, dict)}
    assert {"sqlalchemy", "asyncpg", "psycopg"}.issubset(names)
