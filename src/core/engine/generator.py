# src/core/engine/generator.py
# Updated: 2025-09-01 20:50 - Full distribution test
import importlib
import importlib.util
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

# Use package-relative imports to avoid creating duplicate module objects
# when the package is imported as `src.*` by the tests.
from core.config.kit_config import KitConfig, Variable, VariableType
from core.exceptions import TemplateError, ValidationError
from core.hooks.hook_runner import HookRunner
from core.rendering.template_renderer import TemplateRenderer
from core.structure.structure_builder import StructureBuilder


class BaseKitGenerator(ABC):
    """Abstract base class for all kit generators.

    Subclasses must implement :meth:`extra_context` to provide additional
    template variables specific to the kit.
    """

    def __init__(self, kit_path: Path, config: KitConfig):
        self.kit_path = kit_path
        self.config = config
        self.template_renderer = TemplateRenderer(kit_path / "templates")
        # Set after generate() starts; kept optional for lifecycle clarity
        self.structure_builder: Optional[StructureBuilder] = None

    @abstractmethod
    def extra_context(self) -> Dict[str, Any]:  # pragma: no cover - interface
        """Return extra template context specific to the concrete kit."""

    def generate(self, output_path: Path, variables: Dict[str, Any]) -> List[str]:
        validated_vars = self._validate_and_normalize_variables(variables)
        # allow subclass context hook
        try:
            validated_vars.update(self.extra_context())

            # Provide helpful runtime context values to templates.
            # - Ensure a 'year' variable is available (license templates expect it).
            # - Normalize 'author' so templates receive a user-friendly string instead
            #   of literal Jinja expressions like "{{ getpass.getuser() }}" from kit defaults.
            try:
                import datetime as _dt
                import getpass as _gp

                if not validated_vars.get("year"):
                    validated_vars["year"] = _dt.date.today().year

                a = validated_vars.get("author")
                # If author contains a Jinja placeholder string (from kit defaults)
                # or seems empty, replace with the current system user for nicer
                # generated output.
                if not a or (isinstance(a, str) and ("{{" in a or "getpass" in a)):
                    validated_vars["author"] = _gp.getuser()
            except (OSError, KeyError, RuntimeError):
                # Be resilient if getpass / datetime fail for any rare reason.
                # Catch only specific known exception classes instead of a blind
                # `except Exception` to satisfy linters and make errors explicit.
                pass
        except Exception as e:  # pragma: no cover - defensive
            raise RuntimeError(f"Failed to build extra context: {e}") from e

        HookRunner.run(self.kit_path, self.config.hooks.get("pre_generate", ""), validated_vars)

        # Initialize structure builder once per generate call
        builder = StructureBuilder(output_path)
        builder.clean_output()
        self.structure_builder = builder

        created_files: List[str] = []
        for item in self.config.structure:
            if not self._check_conditions(item.conditions, validated_vars):
                continue
            full_path = output_path / item.path
            template_path: Optional[str] = None
            if item.template:
                template_path = item.template
            elif hasattr(item, "template_if") and item.template_if:
                key_val = validated_vars.get("license")
                if isinstance(key_val, str):  # guard Optional[Any]
                    template_path = item.template_if.get(
                        key_val
                    )  # noqa: B905 (safe indexed access)
            if template_path:
                try:
                    content = self.template_renderer.render(template_path, validated_vars)
                    builder.write_file(item.path, content, overwrite=True)
                    created_files.append(str(full_path))
                except TemplateError as e:
                    raise TemplateError(f"Error rendering {template_path}: {e}") from e
            elif item.content:
                builder.write_file(item.path, item.content, overwrite=True)
                created_files.append(str(full_path))
            elif item.path.endswith("/"):
                builder.create_directory(item.path)
            else:
                builder.write_file(item.path, "", overwrite=True)
                created_files.append(str(full_path))

        HookRunner.run(
            self.kit_path,
            self.config.hooks.get("post_generate", ""),
            validated_vars,
            output_path,
        )
        return created_files

    def _run_hook(
        self,
        hook_name: str,
        variables: Dict[str, Any],
        output_path: Optional[Path] = None,
    ) -> None:
        if hook_name not in self.config.hooks:
            return

        hook_path = self.kit_path / "hooks.py"
        if not hook_path.exists():
            return

        try:
            spec = importlib.util.spec_from_file_location("kit_hooks", hook_path)
            if not spec or not spec.loader:
                raise ImportError("Invalid spec for kit_hooks")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            hook_func_name = self.config.hooks[hook_name]
            # Hook funcs have two possible signatures:
            # pre_generate: (variables: Dict[str, Any]) -> None
            # post_generate: (output_path: Path, variables: Dict[str, Any]) -> None
            hook_func = getattr(module, hook_func_name)

            if hook_name == "pre_generate":
                hook_func(variables)  # runtime dynamic call
            else:
                hook_func(output_path, variables)

        except (AttributeError, FileNotFoundError, ImportError) as e:
            raise RuntimeError(f"Failed to run hook '{hook_name}': {e}") from e

    def _validate_and_normalize_variables(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        validated = variables.copy()

        for var in self.config.variables:
            if var.name not in validated:
                if var.required:
                    raise ValidationError(f"Missing required variable '{var.name}'")
                validated[var.name] = var.default
            validated[var.name] = self._convert_variable_type(var, validated[var.name])

        return validated

    def _convert_variable_type(self, var: Variable, value: Any) -> Any:
        """Convert a variable value to its declared type with validation.

        Single-return implementation to satisfy PLR0911 while keeping logic clear.
        """
        result = value
        if var.type == VariableType.STRING:
            result = str(value)
        elif var.type == VariableType.INTEGER:
            try:
                result = int(value)
            except (TypeError, ValueError) as err:  # pragma: no cover - defensive
                raise ValidationError(f"Variable '{var.name}' must be an integer") from err
        elif var.type == VariableType.BOOLEAN:
            result = str(value).lower() in ("true", "1", "yes", "on")
        elif var.type == VariableType.LIST:
            if isinstance(value, list):
                result = value
            else:
                result = [x.strip() for x in str(value).split(",")]
        elif var.type == VariableType.CHOICE:
            if var.choices and value not in var.choices:
                raise ValidationError(f"Variable '{var.name}' must be one of {var.choices}")
            result = value
        return result

    def _check_conditions(self, conditions: Dict[str, Any], variables: Dict[str, Any]) -> bool:
        if not conditions:
            return True
        return all(variables.get(key) == val for key, val in conditions.items())
