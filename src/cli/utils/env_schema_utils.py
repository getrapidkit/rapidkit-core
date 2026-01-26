import importlib.util
from pathlib import Path
from typing import Any, Dict


def collect_env_schemas(modules_path: Path) -> Dict[str, Any]:
    merged: Dict[str, Any] = {}
    for module_dir in modules_path.iterdir():
        schema_path = module_dir / "config" / "env_schema.py"
        if schema_path.exists():
            spec = importlib.util.spec_from_file_location(
                f"env_schema_{module_dir.name}", str(schema_path)
            )
            if not spec or not spec.loader:  # defensive guard
                continue
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
            except (
                ImportError,
                OSError,
                AttributeError,
                SyntaxError,
            ):  # narrow exceptions
                continue
            env_schema = getattr(mod, "ENV_SCHEMA", {}) or {}
            if isinstance(env_schema, dict):
                merged.update(env_schema)
    return merged
