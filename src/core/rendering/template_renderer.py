# src / core / rendering / template_renderer.py

import re
import secrets
import string
from pathlib import Path
from typing import Any, Dict

from jinja2 import (
    ChoiceLoader,
    Environment,
    FileSystemLoader,
    StrictUndefined,
    TemplateError,
    TemplateNotFound,
    select_autoescape,
)


class TemplateRenderer:

    @staticmethod
    def unique(seq, attribute=None, reverse: bool = False):  # type: ignore[no-untyped-def]
        seen = set()
        result = []
        items = reversed(seq) if reverse else seq
        for item in items:
            key = getattr(item, attribute) if attribute else item
            if key not in seen:
                seen.add(key)
                result.append(item)
        return reversed(result) if reverse else result

    def __init__(self, templates_path: Path):
        provided_path = Path(templates_path)
        self.template_root = provided_path.resolve()
        self.templates_path = self.template_root
        templates_root = Path(__file__).parent.parent.parent / "kits"
        base_templates_path = templates_root / "base" / "templates"
        kit_common_path = self.template_root.parent / "common"

        loaders = [FileSystemLoader(str(self.template_root))]
        # Kits may provide sibling `common` directories for shared assets
        if kit_common_path.exists():
            loaders.append(FileSystemLoader(str(kit_common_path)))
        loaders.append(FileSystemLoader(str(base_templates_path)))

        self.env = Environment(
            loader=ChoiceLoader(loaders),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=select_autoescape(),
        )

        self.env.filters.update(
            {
                "snake_case": self.snake_case,
                "pascal_case": self.pascal_case,
                "kebab_case": self.kebab_case,
                "generate_secret": self.generate_secret,
                "unique": self.unique,
            }
        )

    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound as exc:
            fallback_candidates = []
            direct_path = self.templates_path / template_name
            fallback_candidates.append(direct_path)
            try:
                resolved_path = direct_path.resolve()
            except OSError:
                resolved_path = None
            if resolved_path is not None and resolved_path != direct_path:
                fallback_candidates.append(resolved_path)

            for fallback_path in fallback_candidates:
                try:
                    source = fallback_path.read_text(encoding="utf-8")
                except OSError:
                    continue
                template = self.env.from_string(source)
                return template.render(**context)
            raise TemplateError(f"Template '{template_name}' not found") from exc
        except TemplateError as e:
            raise TemplateError(f"Error rendering template '{template_name}': {e}") from e

    # --- Custom Filters ---
    @staticmethod
    def snake_case(text: str) -> str:
        text = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", text)
        text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text)
        return re.sub(r"[^a-z0-9_]", "_", text).lower()

    @staticmethod
    def pascal_case(text: str) -> str:
        return "".join(word.capitalize() for word in re.split(r"[\s_-]+", text))

    @staticmethod
    def kebab_case(text: str) -> str:
        text = re.sub(r"(.)([A-Z][a-z]+)", r"\1-\2", text)
        text = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", text)
        return re.sub(r"[^a-z0-9-]", "-", text).lower()

    @staticmethod
    def generate_secret(_value: Any = None, length: int = 32) -> str:
        # Jinja2 filter invocation passes the left-hand value as the first
        # argument; accept an unused 'value' parameter so the filter can be
        # invoked either as a function ({{ generate_secret(48) }}) or as a
        # filter ({{ '' | generate_secret(48) }}).
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))


def render_template(template_path: Path, variables: Dict[str, Any]) -> str:
    env = Environment(
        loader=FileSystemLoader(template_path.parent),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
        autoescape=select_autoescape(),
    )
    template = env.get_template(template_path.name)
    return template.render(**variables)
