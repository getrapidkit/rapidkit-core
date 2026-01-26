"""Shared generator utilities for all modules."""

from __future__ import annotations

import contextlib
import logging
import re
import secrets
import string
import tempfile
from collections.abc import Mapping as MappingABC
from pathlib import Path
from typing import Any, Mapping, Optional, cast

from modules.shared.exceptions import ModuleGeneratorError

logger = logging.getLogger(__name__)

# Declare placeholders so static type checkers accept assignments and names exist if Jinja2 is missing.
JinjaEnvironment: Optional[Any] = None
FileSystemLoader: Optional[Any] = None
StrictUndefined: Optional[Any] = None
select_autoescape: Optional[Any] = None

with contextlib.suppress(ImportError):  # pragma: no cover - optional dependency during bootstrap
    from jinja2 import (
        Environment as JinjaEnvironment,
        FileSystemLoader,
        StrictUndefined,
        select_autoescape,
    )

DEFAULT_ENCODING = "utf-8"


class CustomTemplateParser:
    """Robust custom template parser with variable and filter support.

    Supports basic template syntax:
    - Variables: {{ variable_name }}
    - Filters: {{ variable_name|filter_name }}
    - Nested access: {{ config.database.host }} (basic support)
    """

    def __init__(self) -> None:
        # Regex patterns for template parsing
        self.variable_pattern = re.compile(r"\{\{\s*([^|\s}]+)\s*\}\}")
        self.filter_pattern = re.compile(r"\{\{\s*([^|]+?)\s*\|\s*(\w+)(?:\((.*?)\))?\s*\}\}")
        self.nested_pattern = re.compile(r"\{\{\s*([^\s}]+)\s*\}\}")

        # Available filters
        self.filters = {
            "upper": lambda value, *_: str(value).upper(),
            "lower": lambda value, *_: str(value).lower(),
            "len": lambda value, *_: len(value) if hasattr(value, "__len__") else 0,
            "strip": lambda value, *_: str(value).strip(),
            "title": lambda value, *_: str(value).title(),
            # Generate a cryptographically-strong secret. When used as a filter
            # invocation the left-hand value may be passed as the first argument;
            # accept and ignore it for convenience. The custom parser forwards
            # the string of args as the second parameter.
            "generate_secret": lambda _value, raw_args=None, *_: (
                self._generate_secret_helper(
                    int(raw_args.strip()) if (raw_args and raw_args.strip()) else 32
                )
            ),
        }

    class _UndefinedPlaceholder:
        """Sentinel used when a variable cannot be resolved."""

        def __init__(self, expression: str) -> None:
            self.expression = expression.strip()

        def __str__(self) -> str:
            return f"{{{{ {self.expression} }}}}"

        def __bool__(self) -> bool:  # pragma: no cover - bool check keeps template semantics
            return False

    def render(self, content: str, context: Mapping[str, Any]) -> str:
        """Render template content with given context."""
        # Handle filters first (more specific pattern)
        result = self.filter_pattern.sub(
            lambda m: self._apply_filter(
                variable_expr=m.group(1).strip(),
                filter_name=m.group(2),
                filter_args=(m.group(3) or ""),
                context=context,
            ),
            content,
        )

        # Handle simple variables
        result = self.variable_pattern.sub(
            lambda m: self._stringify(self._resolve_variable(m.group(1), context), m.group(1)),
            result,
        )

        return result

    def _apply_filter(
        self,
        *,
        variable_expr: str,
        filter_name: str,
        filter_args: str,
        context: Mapping[str, Any],
    ) -> str:
        """Apply a filter to a resolved variable."""

        value = self._resolve_variable(variable_expr, context)

        if filter_name == "default":
            return self._filter_default(value, filter_args, variable_expr)

        filter_func = self.filters.get(filter_name)
        if filter_func:
            try:
                # mypy can't infer a callable type for items stored in the
                # filters mapping; cast to a callable so static type checks
                # understand this is an intentional dynamic call.
                from typing import Callable

                callable_func = cast(Callable[..., Any], filter_func)
                transformed = callable_func(value, filter_args, variable_expr)
            except (TypeError, ValueError, AttributeError) as exc:
                logger.warning("Filter '%s' failed on value '%s': %s", filter_name, value, exc)
                return self._stringify(value, variable_expr)
            return self._stringify(transformed, variable_expr)

        logger.warning("Unknown filter '%s', returning unfiltered value", filter_name)
        return self._stringify(value, variable_expr)

    def _resolve_variable(self, variable_expr: str, context: Mapping[str, Any]) -> Any:
        """Resolve a variable expression, supporting nested access."""
        try:
            parts = variable_expr.split(".")
            current: Any = context

            for part in parts:
                if isinstance(current, MappingABC):
                    if part in current:
                        current = current[part]
                    else:
                        return self._UndefinedPlaceholder(variable_expr)
                elif hasattr(current, part):
                    current = getattr(current, part)
                else:
                    return self._UndefinedPlaceholder(variable_expr)

            if current is None:
                return ""
            return current

        except (KeyError, AttributeError, TypeError) as exc:
            logger.warning("Failed to resolve variable '%s': %s", variable_expr, exc)
            return self._UndefinedPlaceholder(variable_expr)

    def _stringify(self, value: Any, variable_expr: str) -> str:
        if isinstance(value, self._UndefinedPlaceholder):
            return str(value)
        if value is None:
            return ""
        return str(value)

    def _filter_default(self, value: Any, raw_args: str, variable_expr: str) -> str:
        args = [part.strip() for part in raw_args.split(",", 1)] if raw_args else [""]
        fallback = args[0] if args else ""
        boolean_mode = False
        if len(args) > 1:
            boolean_mode = args[1].lower() in {"true", "1", "yes", "on"}

        is_missing = isinstance(value, self._UndefinedPlaceholder)
        if is_missing:
            return fallback

        if boolean_mode and not value:
            return fallback

        return self._stringify(value, variable_expr)

    @staticmethod
    def _generate_secret_helper(length: int = 32) -> str:
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))


class TemplateRenderer:
    """Render Jinja2 templates with custom parser fallback for maximum reliability."""

    _CONTROL_TAG_MARKERS = ("{%", "{#")

    def __init__(self, template_root: Path) -> None:
        self.template_root = template_root.resolve()
        self.jinja_env: Optional[Any] = None
        self.custom_parser = CustomTemplateParser()

        # Try to initialize Jinja2 environment
        self._initialize_jinja2()

    def _initialize_jinja2(self) -> None:
        """Initialize Jinja2 environment if available."""
        if JinjaEnvironment is None or FileSystemLoader is None or StrictUndefined is None:
            logger.debug("Jinja2 not available, will use custom parser")
            return

        try:
            loader = FileSystemLoader(str(self.template_root))
            self.jinja_env = JinjaEnvironment(
                loader=loader,
                autoescape=False,  # nosec B701 - templates render trusted code artifacts for generators
                keep_trailing_newline=True,
                lstrip_blocks=False,
                trim_blocks=False,
                undefined=StrictUndefined,
            )
            # Register helpful filters for use in templates (keep logic local to
            # this renderer, but consistent with core TemplateRenderer).
            import contextlib

            with contextlib.suppress(AttributeError, TypeError):
                self.jinja_env.filters.update(
                    {
                        "generate_secret": lambda _value=None, length=32: self.custom_parser._generate_secret_helper(
                            int(length)
                            if isinstance(length, (str, int)) and str(length).strip()
                            else 32
                        )
                    }
                )
            logger.debug("Jinja2 environment initialized successfully")
        except (ImportError, OSError, ValueError) as e:
            logger.warning(f"Failed to initialize Jinja2 environment: {e}")
            self.jinja_env = None

    def render(self, template_path: Path, context: Mapping[str, Any]) -> str:
        """Render template with given context, using Jinja2 if available, custom parser as fallback."""
        jinja_error: Optional[Exception] = None
        # Try Jinja2 first for full feature support
        if self.jinja_env is not None:
            try:
                normalized_path = template_path
                if not normalized_path.is_absolute():
                    normalized_path = (self.template_root / normalized_path).resolve()
                else:
                    normalized_path = normalized_path.resolve()

                try:
                    relative_identifier = normalized_path.relative_to(self.template_root)
                    template_name = relative_identifier.as_posix()
                except ValueError:
                    from os import path as osp

                    template_name = osp.relpath(str(normalized_path), str(self.template_root))
                    template_name = template_name.replace("\\", "/")

                template = self.jinja_env.get_template(template_name)
                result = cast(str, template.render(**context))
                logger.debug(f"Rendered {template_path} using Jinja2")
                return result
            except (OSError, ValueError, TypeError, AttributeError) as e:
                logger.warning(
                    f"Jinja2 rendering failed for {template_path}, falling back to custom parser: {e}"
                )
                jinja_error = e

        # Fallback to custom parser
        try:
            normalized_path = template_path
            if not normalized_path.is_absolute():
                normalized_path = (self.template_root / normalized_path).resolve()
            else:
                normalized_path = normalized_path.resolve()
            content = normalized_path.read_text(encoding=DEFAULT_ENCODING)
            if self.jinja_env is None and self._template_requires_jinja(content):
                context_payload = {
                    "template_path": str(template_path),
                    "jinja2_available": self.jinja_env is not None,
                }
                if jinja_error is not None:
                    context_payload["jinja_error"] = str(jinja_error)
                raise ModuleGeneratorError(
                    "Template includes Jinja control structures but Jinja2 rendering is unavailable",
                    context=context_payload,
                )
            result = self.custom_parser.render(content, context)
            logger.debug(f"Rendered {normalized_path} using custom parser")
            return result
        except (OSError, UnicodeDecodeError, ValueError) as e:
            raise ModuleGeneratorError(
                f"Failed to render template with both Jinja2 and custom parser: {template_path}",
                context={
                    "template_path": str(template_path),
                    "jinja2_available": self.jinja_env is not None,
                    "error": str(e),
                },
            ) from e

    def render_template(self, template_identifier: str | Path, context: Mapping[str, Any]) -> str:
        """Compatibility wrapper accepting string paths relative to the template root."""

        normalized_path: Path
        if isinstance(template_identifier, str):
            normalized_path = Path(template_identifier)
        else:
            normalized_path = template_identifier
        return self.render(normalized_path, context)

    @classmethod
    def _template_requires_jinja(cls, content: str) -> bool:
        return any(marker in content for marker in cls._CONTROL_TAG_MARKERS)


def write_file(destination: Path, content: str, *, encoding: str = DEFAULT_ENCODING) -> None:
    """Write content to file, creating parent directories as needed."""
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding=encoding)
    except Exception as e:
        raise ModuleGeneratorError(
            f"Failed to write file: {destination}",
            context={"destination": str(destination), "error": str(e)},
        ) from e


def create_temp_directory(prefix: str = "module-gen-") -> Path:
    """Create a temporary directory for module generation."""
    return Path(tempfile.mkdtemp(prefix=prefix))


def validate_template_exists(template_path: Path, *, context_name: str = "template") -> None:
    """Validate that a template file exists."""
    if not template_path.exists():
        raise ModuleGeneratorError(
            f"Template file not found: {template_path}",
            context={
                "template_path": str(template_path),
                "context": context_name,
                "exists": template_path.exists(),
                "parent_exists": template_path.parent.exists(),
            },
        )


def format_missing_dependencies(details: Mapping[str, str]) -> str:
    """Format missing dependency information for user display."""
    if not details:
        return ""
    lines = ["Missing optional dependencies detected:"]
    for package, hint in details.items():
        lines.append(f"  - {package}: {hint}")
    return "\n".join(lines)


__all__ = [
    "CustomTemplateParser",
    "TemplateRenderer",
    "format_missing_dependencies",
    "create_temp_directory",
    "validate_template_exists",
    "write_file",
    "select_autoescape",
]
