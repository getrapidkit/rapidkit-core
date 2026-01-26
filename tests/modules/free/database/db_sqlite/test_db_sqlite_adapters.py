"""FastAPI adapter integration tests for Db Sqlite."""

from __future__ import annotations

from pathlib import Path

import pytest

fastapi = pytest.importorskip("fastapi")
testclient = pytest.importorskip("fastapi.testclient")

FastAPI = fastapi.FastAPI
TestClient = testclient.TestClient


def test_fastapi_routes_expose_health_and_tables(
    generated_db_sqlite_modules, tmp_path: Path
) -> None:
    modules = generated_db_sqlite_modules
    runtime_module = modules.base
    runtime = runtime_module.DbSqlite(
        runtime_module.DbSqliteConfig(database_path=str(tmp_path / "api.db"))
    )
    runtime.execute("CREATE TABLE products(id INTEGER PRIMARY KEY, name TEXT)", commit=True)

    app = FastAPI()
    modules.fastapi_runtime.register_fastapi(app, runtime=runtime)
    client = TestClient(app)

    health_response = client.get("/db-sqlite/health")
    assert health_response.status_code == 200
    payload = health_response.json()
    assert payload["status"] == "ok"
    assert payload["module"] == "db_sqlite"

    tables_response = client.get("/db-sqlite/tables")
    assert tables_response.status_code == 200
    tables = tables_response.json()
    assert any(table["name"] == "products" for table in tables)

    runtime.close()
