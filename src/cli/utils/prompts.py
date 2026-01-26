# src / cli / utils / prompts.py
from typing import Any, Dict

import click

from core.config.kit_config import KitConfig, VariableType


def prompt_variables(
    kit_config: KitConfig, existing_vars: Dict[str, Any], interactive: bool = False
) -> Dict[str, Any]:
    """Prompt user for missing or all variables"""

    variables = existing_vars.copy()

    click.echo()
    click.echo("📝 Configuration Setup")
    click.echo("-" * 20)

    for var in kit_config.variables:
        # Skip project_name as it's provided as argument
        if var.name == "project_name":
            continue

        # Skip if not interactive and variable already provided
        if not interactive and var.name in variables:
            continue

        # Skip optional variables in non-interactive mode
        if not interactive and not var.required:
            continue

        current_value = variables.get(var.name)
        prompt_text = f"{var.name}"
        if var.description:
            prompt_text += f" ({var.description})"

        if var.type == VariableType.BOOLEAN:
            default_val = current_value if current_value is not None else var.default
            value = click.confirm(prompt_text, default=default_val)

        elif var.type == VariableType.CHOICE:
            choices = tuple(var.choices or ())
            default_val = current_value if current_value is not None else var.default
            value = click.prompt(
                prompt_text,
                type=click.Choice(choices),
                default=default_val,
                show_default=True,
            )

        elif var.type == VariableType.INTEGER:
            default_val = current_value if current_value is not None else var.default
            value = click.prompt(prompt_text, type=int, default=default_val, show_default=True)

        else:  # STRING or LIST
            default_val = current_value if current_value is not None else var.default
            if var.required and not default_val:
                value = click.prompt(prompt_text)
            else:
                value = click.prompt(prompt_text, default=default_val, show_default=True)

        variables[var.name] = value

    return variables
