import os
import re
from typing import Any, Dict, List, Optional, Union

import typer

from ..ui.printer import print_error


def _validate_scalar(value: str, pattern: Optional[str], var_name: str) -> None:
    if pattern:
        if not re.match(pattern, str(value)):
            raise typer.BadParameter(
                f"Value '{value}' for '{var_name}' does not match pattern '{pattern}'"
            )


def _validate_list(values: List[str], item_pattern: Optional[str], var_name: str) -> None:
    if item_pattern:
        for idx, v in enumerate(values):
            if not re.match(item_pattern, str(v)):
                raise typer.BadParameter(
                    f"Item #{idx+1}='{v}' for '{var_name}' does not match pattern '{item_pattern}'"
                )


def prompt_for_variables(variables_config: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Prompt for required variables or use defaults/env variables.
    Supports regex validation for scalars via `validation` and list items via `item_validation`.
    """
    variables: Dict[str, Any] = {}
    for var, meta in variables_config.items():
        env_var_name = var.upper()
        env_raw = os.environ.get(env_var_name)

        vtype_raw = meta.get("type")
        vtype = str(vtype_raw).lower() if vtype_raw else "string"
        is_required = bool(meta.get("required", False))
        default: Any = meta.get("default", [] if vtype == "list" else "")
        description = meta.get("description", "")
        validation = meta.get("validation")  # for scalar
        item_validation = meta.get("item_validation")  # for list items

        # Compose value from env/default/prompt
        value: Union[str, int, bool, List[str]]
        if env_raw is not None:
            if vtype == "list":
                # os.environ only supplies str; split by comma
                env_str = str(env_raw)
                value = [x.strip() for x in env_str.split(",") if x.strip()]
            elif vtype == "bool":
                value = str(env_raw).lower() in {"1", "true", "yes", "on"}
            elif vtype == "int":
                try:
                    value = int(env_raw)
                except (ValueError, TypeError) as err:
                    raise typer.BadParameter(
                        f"Environment variable {env_var_name} must be an integer"
                    ) from err
            else:
                value = str(env_raw)
        elif is_required:
            prompt_text = f"🔑 Enter value for required variable '{var}' ({description})"
            if vtype == "list":
                raw = typer.prompt(prompt_text + " [comma-separated]")
                value = [x.strip() for x in raw.split(",") if x.strip()]
            elif vtype == "bool":
                value = bool(typer.confirm(prompt_text))
            elif vtype == "int":
                value = int(typer.prompt(prompt_text))
            else:
                value = typer.prompt(prompt_text)
        else:
            value = default

        # Validation
        try:
            if vtype == "list":
                if not isinstance(value, list):
                    value = [] if value in {"", None} else [str(value)]
                value = [str(x) for x in value]
                _validate_list(value, item_validation, var)
            else:
                _validate_scalar(str(value), validation, var)
        except typer.BadParameter as e:
            print_error(str(e))
            raise

        variables[var] = value

    return variables
