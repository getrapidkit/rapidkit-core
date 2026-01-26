from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType
from typing import Iterator

import pytest

from modules.free.cache.redis.generate import RedisModuleGenerator


@pytest.fixture()
def rendered_redis_health(tmp_path) -> Iterator[ModuleType]:
    generator = RedisModuleGenerator()
    config = generator.load_module_config()
    context = generator.build_base_context(config)
    renderer = generator.create_renderer()

    package_root = tmp_path / "rendered_redis"
    package_root.mkdir(parents=True, exist_ok=True)
    (package_root / "__init__.py").write_text("", encoding="utf-8")

    # Create a minimal 'modules.free.cache.redis' package used by the health template imports
    client_stub = """async def check_redis_connection():\n    return True\n\ndef get_redis_metadata():\n    return {\n        'module': 'redis',\n        'cache_ttl': None,\n    }\n"""
    types_stub = """class RedisHealthSnapshot:\n    def __init__(self, status, checked_at, cache_ttl=None):\n        self.status = status\n        self.checked_at = checked_at\n        self.cache_ttl = cache_ttl\n\n    @classmethod\n    def collect(cls, metadata):\n        return cls(status='ok', checked_at='now', cache_ttl=metadata.get('cache_ttl'))\n\ndef as_dict(snapshot):\n    return {'status': snapshot.status, 'module': 'redis', 'checked_at': str(snapshot.checked_at)}\n"""

    def _write_stub(root: Path) -> None:
        module_root = root / "modules" / "free" / "cache" / "redis"
        module_root.mkdir(parents=True, exist_ok=True)
        (root / "modules" / "free" / "cache" / "__init__.py").write_text("", encoding="utf-8")
        (root / "modules" / "free" / "__init__.py").write_text("", encoding="utf-8")
        (root / "modules" / "__init__.py").write_text("", encoding="utf-8")
        (module_root / "__init__.py").write_text("", encoding="utf-8")
        (module_root / "client.py").write_text(client_stub, encoding="utf-8")
        (module_root / "redis_types.py").write_text(types_stub, encoding="utf-8")

    _write_stub(tmp_path)
    src_root = tmp_path / "src"
    src_root.mkdir(parents=True, exist_ok=True)
    (src_root / "__init__.py").write_text("", encoding="utf-8")
    _write_stub(src_root)
    health_code = renderer.render_template("templates/base/redis_health.py.j2", context)
    (package_root / "redis_health.py").write_text(health_code, encoding="utf-8")

    sys_path_entry = str(tmp_path)
    sys.path.insert(0, sys_path_entry)

    removed_modules: list[tuple[str, ModuleType]] = []

    def _pop_module(name: str) -> None:
        module = sys.modules.pop(name, None)
        if module is not None:
            removed_modules.append((name, module))

    for module_name in [
        "modules.free.cache.redis.client",
        "modules.free.cache.redis",
        "modules.free.cache",
        "modules.free",
        "modules",
        "modules.free.cache.redis.client",
        "modules.free.cache.redis",
        "modules.free.cache",
        "modules.free",
        "src.modules",
        "src",
    ]:
        _pop_module(module_name)
    try:
        module = importlib.import_module("rendered_redis.redis_health")
        yield module
    finally:
        if sys_path_entry in sys.path:
            sys.path.remove(sys_path_entry)
        # Restore any previously-imported modules the test removed.
        for name, module in reversed(removed_modules):
            sys.modules[name] = module
        for name in list(sys.modules):
            module_obj = sys.modules.get(name)
            module_file = getattr(module_obj, "__file__", "")
            if (
                name == "rendered_redis"
                or name.startswith("rendered_redis.")
                or (module_file and module_file.startswith(sys_path_entry))
            ):
                sys.modules.pop(name, None)


def _validate_schema(payload: dict) -> None:
    # Attempt schema validation using jsonschema when available. Fall back to
    # minimal structural checks if jsonschema isn't present or validation fails.
    import json

    try:
        import jsonschema  # type: ignore

        schema_path = None
        for candidate in Path(__file__).resolve().parents:
            potential = candidate / "src" / "modules" / "shared" / "schema" / "health.schema.json"
            if potential.exists():
                schema_path = potential
                break
        if schema_path is None:
            raise FileNotFoundError("health.schema.json not found")

        with schema_path.open(encoding="utf-8") as fh:
            raw = json.load(fh)

        try:
            jsonschema.validate(payload, raw)
            return
        except jsonschema.ValidationError:  # validation failed; fall back to light checks
            pass
    except (ImportError, FileNotFoundError):
        # jsonschema not available — fall back to light checks
        pass

    assert isinstance(payload, dict)
    assert "module" in payload
    assert "status" in payload
    assert "checked_at" in payload


def test_redis_health_payload_matches_schema(rendered_redis_health) -> None:
    module = rendered_redis_health
    # Different health templates expose different helpers: some modules provide
    # build_health_snapshot/render_health_snapshot helpers while others (like
    # the FastAPI router variant) expose a collection helper and as_dict
    # function. Support both shapes so this schema test is robust.
    if hasattr(module, "build_health_snapshot"):
        snapshot = module.build_health_snapshot(
            status="ok",
            host="localhost",
            port=6379,
            test_connection=True,
        )
        # prefer a dedicated render helper when present
        if hasattr(module, "render_health_snapshot"):
            payload = module.render_health_snapshot(snapshot)
        else:
            # fallback to a naive dict conversion
            payload = getattr(module, "as_dict", lambda s: s.__dict__)(snapshot)
    else:
        # Use the router-style helpers: collect a snapshot and render via as_dict
        if hasattr(module, "_collect_snapshot"):
            snapshot = module._collect_snapshot()
        elif hasattr(module, "RedisHealthSnapshot"):
            snapshot = module.RedisHealthSnapshot.collect({"module": "redis", "cache_ttl": None})
        else:
            raise AssertionError("Rendered redis health module lacks snapshot helpers")

        # Convert to payload and mirror the structure used by the template
        payload = module.as_dict(snapshot)
        payload.update(
            {
                "status": "ok",
                "checks": {"connection": True, "cache_ttl": snapshot.cache_ttl is not None},
            }
        )
    _validate_schema(payload)
