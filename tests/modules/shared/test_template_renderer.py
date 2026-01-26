import textwrap

import pytest

from modules.shared import generator as generator_module
from modules.shared.exceptions import ModuleGeneratorError
from modules.shared.generator import CustomTemplateParser, TemplateRenderer


def test_custom_parser_handles_default_filter_for_missing_value() -> None:
    parser = CustomTemplateParser()
    template = textwrap.dedent(
        """
        ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default={{ ACCESS_TOKEN_EXPIRE_MINUTES | default(15) }})
        """
    ).strip()

    rendered = parser.render(template, {})

    assert rendered == "ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15)"


def test_custom_parser_default_filter_boolean_mode() -> None:
    parser = CustomTemplateParser()
    template = "value={{ name | default('fallback', true) }}"

    rendered = parser.render(template, {"name": ""})

    assert rendered == "value='fallback'"


def test_custom_parser_default_filter_respects_existing_value() -> None:
    parser = CustomTemplateParser()
    template = "value={{ name | default('fallback') }}"

    rendered = parser.render(template, {"name": "kept"})

    assert rendered == "value=kept"


def _disable_jinja(monkeypatch) -> None:
    monkeypatch.setattr(generator_module, "JinjaEnvironment", None, raising=False)
    monkeypatch.setattr(generator_module, "FileSystemLoader", None, raising=False)
    monkeypatch.setattr(generator_module, "StrictUndefined", None, raising=False)


def test_template_renderer_requires_jinja_for_control_tags(tmp_path, monkeypatch) -> None:
    _disable_jinja(monkeypatch)
    template_path = tmp_path / "control.j2"
    template_path.write_text("{% if flag %}ok{% endif %}", encoding="utf-8")

    renderer = TemplateRenderer(tmp_path)

    with pytest.raises(ModuleGeneratorError):
        renderer.render(template_path, {})


def test_template_renderer_fallback_works_for_simple_expressions(tmp_path, monkeypatch) -> None:
    _disable_jinja(monkeypatch)
    template_path = tmp_path / "simple.j2"
    template_path.write_text("value={{ name | default('fallback') }}", encoding="utf-8")

    renderer = TemplateRenderer(tmp_path)

    rendered = renderer.render(template_path, {})

    assert rendered == "value='fallback'"
