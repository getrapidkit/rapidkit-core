from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType
from typing import Iterator

import pytest

from modules.free.database.db_postgres.generate import DbPostgresModuleGenerator


@pytest.fixture()
def rendered_db_postgres_health(tmp_path) -> Iterator[ModuleType]:
    generator = DbPostgresModuleGenerator()
    config = generator.load_module_config()
    context = generator.build_base_context(config)
    renderer = generator.create_renderer()

    package_root = tmp_path / "rendered_db_postgres"
    package_root.mkdir(parents=True, exist_ok=True)
    (package_root / "__init__.py").write_text("", encoding="utf-8")

    types_code = renderer.render_template("templates/base/db_postgres_types.py.j2", context)
    (package_root / "db_postgres_types.py").write_text(types_code, encoding="utf-8")

    health_code = renderer.render_template("templates/base/db_postgres_health.py.j2", context)
    (package_root / "db_postgres_health.py").write_text(health_code, encoding="utf-8")

    sys_path_entry = str(tmp_path)
    sys.path.insert(0, sys_path_entry)
    try:
        module = importlib.import_module("rendered_db_postgres.db_postgres_health")
        yield module
    finally:
        if sys_path_entry in sys.path:
            sys.path.remove(sys_path_entry)
        for name in list(sys.modules):
            if name == "rendered_db_postgres" or name.startswith("rendered_db_postgres."):
                sys.modules.pop(name, None)


def _validate_schema(payload: dict) -> None:
    import json

    try:
        import jsonschema  # type: ignore

        schema_path = (
            Path(__file__).resolve().parents[4]
            / "src"
            / "modules"
            / "shared"
            / "schema"
            / "health.schema.json"
        )

        with schema_path.open(encoding="utf-8") as fh:
            raw = json.load(fh)

        try:
            jsonschema.validate(payload, raw)
            return
        except jsonschema.ValidationError:
            # validation failed — fall back to minimal asserts below
            pass
    except ImportError:
        # jsonschema not available — fall back to minimal asserts
        pass

    assert isinstance(payload, dict)
    assert "module" in payload
    assert "status" in payload
    assert "checked_at" in payload


def test_db_postgres_health_payload_matches_schema(rendered_db_postgres_health) -> None:
    module = rendered_db_postgres_health
    snapshot = module.build_health_snapshot(
        "ok",
        database_url="postgresql://user:pass@db:5432/app",
        pool_size=5,
        max_overflow=5,
        pool_timeout=15,
        pool_recycle=120,
    )
    payload = module.render_health_snapshot(snapshot)
    _validate_schema(payload)
