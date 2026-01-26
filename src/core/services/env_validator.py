"""Smart ENV validator used by snippet injector and modules.

Features:
 - Schema driven (types, choices, regex, item validation)
 - Custom callables via import path
 - Lenient mode applying defaults while collecting errors
"""

from __future__ import annotations

import importlib
import os
import re
from typing import Any, Callable, Dict, List, Optional, Tuple, cast
from urllib.parse import urlparse

ENV_SCHEMA: Dict[str, Dict[str, Any]] = {
    "ENV": {
        "type": "str",
        "default": "development",
        "choices": ["development", "production", "staging"],
    },
    "DEBUG": {"type": "bool", "default": False},
    "PROJECT_NAME": {"type": "str", "default": "RapidKit App"},
    "SECRET_KEY": {"type": "str", "default": "changeme"},
    "VERSION": {"type": "str", "default": "1.0.0"},
    "ALLOWED_HOSTS": {"type": "str", "default": "*"},
    "LOG_LEVEL": {
        "type": "str",
        "default": "INFO",
        "choices": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    },
    "VAULT_URL": {"type": "str", "default": "http://localhost:8200"},
    "AWS_REGION": {"type": "str", "default": "us-east-1"},
}


def parse_bool(val: str) -> bool:
    lowered = val.strip().lower()
    if lowered in {"1", "true", "yes", "on", "y", "t"}:
        return True
    if lowered in {"0", "false", "no", "off", "n", "f"}:
        return False
    raise ValueError(f"invalid boolean value: '{val}'")


def cast_value(val: str, typ: str) -> Any:
    if typ == "bool":
        return parse_bool(val)
    if typ == "int":
        return int(val)
    if typ == "float":
        return float(val)
    if typ == "list":
        return [p.strip() for p in val.split(",") if p.strip()]
    return val


def is_valid_url(val: str) -> bool:
    try:
        parsed = urlparse(val)
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


TWO_PARTS = 2  # sentinel for split length comparisons
TWO_RESULT_ITEMS = 2  # expected length from custom validator tuple result


def _load_callable(path: str) -> Callable[..., Any]:
    if ":" in path:
        module_path, func_name = path.split(":", 1)
    else:
        parts = path.rsplit(".", 1)
        if len(parts) != TWO_PARTS:
            raise ImportError(f"Invalid callable path: {path}")
        module_path, func_name = parts
    mod = importlib.import_module(module_path)
    func = getattr(mod, func_name)
    return cast(Callable[..., Any], func)


def validate_env(
    env_dict: Dict[str, str],
    schema: Dict[str, Dict[str, Any]] = ENV_SCHEMA,
    *,
    lenient: bool = False,
) -> Tuple[Dict[str, Any], bool, List[str]]:
    validated: Dict[str, Any] = {}
    is_valid = True
    errors: List[str] = []

    for key, meta in schema.items():
        raw_val = env_dict.get(key)
        typ = meta.get("type", "str")
        default = meta.get("default")
        choices = meta.get("choices")
        required = bool(meta.get("required", False))
        validation = meta.get("validation")
        item_validation = meta.get("item_validation")
        custom_validator = meta.get("custom_validator")

        if raw_val is None:
            if required:
                errors.append(f"{key} required but not set")
                is_valid = False
            validated[key] = default
            continue

        try:
            if custom_validator:
                if isinstance(custom_validator, str):
                    func = _load_callable(custom_validator)
                elif callable(custom_validator):
                    func = custom_validator
                else:
                    raise ValueError("custom_validator must be callable or import path")
                result = func(raw_val)
                if isinstance(result, tuple) and len(result) == TWO_RESULT_ITEMS:
                    ok, casted = result
                    if not ok:
                        raise ValueError(f"custom validator failed for {key}")
                    val = casted
                else:
                    val = result
            else:
                val = cast_value(raw_val, typ)

            if typ == "bool" and not isinstance(val, bool):
                raise ValueError("not a boolean")
            if typ == "int" and not isinstance(val, int):
                raise ValueError("not an integer")
            if typ == "float" and not isinstance(val, float):
                raise ValueError("not a float")
            if typ == "url":
                if not is_valid_url(raw_val):
                    raise ValueError("invalid url")
                val = raw_val
            if choices and val not in choices:
                raise ValueError(f"value '{raw_val}' not in choices {choices}")
            if validation:
                pattern = re.compile(validation)
                if not pattern.match(str(raw_val)):
                    raise ValueError(f"value '{raw_val}' does not match validation {validation}")
            if typ == "list" and item_validation:
                item_pat = re.compile(item_validation)
                items = (
                    val if isinstance(val, list) else [x.strip() for x in str(raw_val).split(",")]
                )
                for it in items:
                    if not item_pat.match(it):
                        raise ValueError(f"list item '{it}' does not match {item_validation}")
            validated[key] = val
        except (ValueError, TypeError, ImportError, AttributeError) as e:
            errors.append(f"{key} value '{raw_val}' invalid for type {typ}: {e}")
            is_valid = False
            validated[key] = default

    for key, val in env_dict.items():
        if key not in validated:
            validated[key] = val

    if lenient and errors:
        # Lenient mode still reports invalid (is_valid stays False) but
        # defaults have been applied so downstream logic can continue if it
        # chooses to ignore the boolean flag. (Test expectation: lenient keeps failure.)
        pass
    return validated, is_valid, errors


def load_env_file(path: str) -> Dict[str, str]:
    env: Dict[str, str] = {}
    if not os.path.exists(path):
        return env
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def validate_env_file(
    path: str,
    schema: Optional[Dict[str, Dict[str, Any]]] = None,
    *,
    lenient: bool = False,
) -> Tuple[Dict[str, Any], bool, List[str]]:
    env = load_env_file(path)
    return validate_env(env, schema or ENV_SCHEMA, lenient=lenient)


if __name__ == "__main__":  # pragma: no cover
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else ".env"
    validated_env, ok, errs = validate_env_file(target)
    print("VALID:", ok)
    for e in errs:
        print(" -", e)
