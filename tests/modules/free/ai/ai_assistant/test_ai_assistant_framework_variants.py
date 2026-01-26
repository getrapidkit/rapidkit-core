from pathlib import Path
from typing import Iterator

import pytest

from modules.free.ai.ai_assistant.frameworks import (
    FastAPIPlugin,
    NestJSPlugin,
    get_plugin,
    list_available_plugins,
    refresh_plugin_registry,
    register_plugin,
)
from modules.shared.frameworks import FrameworkPlugin


@pytest.fixture(autouse=True)
def reset_registry() -> Iterator[None]:
    """Ensure each test starts with a clean registry state."""

    refresh_plugin_registry(auto_discover=False)
    yield
    refresh_plugin_registry(auto_discover=False)


def test_registry_exposes_builtin_plugins() -> None:
    plugins = list_available_plugins()

    assert plugins["fastapi"] == "FastAPI"
    assert plugins["nestjs"] == "NestJS"
    assert isinstance(get_plugin("fastapi"), FastAPIPlugin)
    assert isinstance(get_plugin("nestjs"), NestJSPlugin)


def test_register_plugin_adds_custom_framework() -> None:
    class DummyPlugin(FrameworkPlugin):
        @property
        def name(self) -> str:
            return "dummy"

        @property
        def display_name(self) -> str:
            return "Dummy"

        @property
        def language(self) -> str:
            return "python"

        def get_template_mappings(self):
            return {}

        def get_output_paths(self):
            return {}

        def get_context_enrichments(self, base_context):
            return dict(base_context, framework="dummy")

        def validate_requirements(self):
            return []

        def get_dependencies(self):
            return []

        def get_dev_dependencies(self):
            return []

        def pre_generation_hook(self, output_dir: Path) -> None:
            _ = output_dir

        def post_generation_hook(self, output_dir: Path) -> None:
            _ = output_dir

    register_plugin(DummyPlugin)

    plugins = list_available_plugins()
    assert "dummy" in plugins
    plugin = get_plugin("dummy")
    assert isinstance(plugin, DummyPlugin)
    assert plugin.get_context_enrichments({})["framework"] == "dummy"


def test_fastapi_plugin_context_and_dependencies(tmp_path: Path) -> None:
    plugin = FastAPIPlugin()
    base_context = {"module_name": "ai_assistant"}

    mappings = plugin.get_template_mappings()
    outputs = plugin.get_output_paths()
    enriched = plugin.get_context_enrichments(base_context)

    assert plugin.name == "fastapi"
    assert plugin.language == "python"
    assert mappings["runtime"].endswith("ai_assistant.py.j2")
    assert outputs["health"].endswith("src/health/ai_assistant.py")
    assert enriched["framework_display_name"] == "FastAPI"
    assert plugin.get_dependencies() == ["fastapi>=0.110.0"]
    assert "pytest-asyncio>=0.23.0" in plugin.get_dev_dependencies()

    output_dir = tmp_path / "fastapi"
    plugin.pre_generation_hook(output_dir)
    assert (output_dir / "src" / "modules" / "free" / "ai" / "ai_assistant").is_dir()
    plugin.post_generation_hook(output_dir)


def test_nestjs_plugin_context_and_dependencies(tmp_path: Path) -> None:
    plugin = NestJSPlugin()
    base_context = {"module_name": "ai_assistant"}

    mappings = plugin.get_template_mappings()
    outputs = plugin.get_output_paths()
    enriched = plugin.get_context_enrichments(base_context)

    assert plugin.name == "nestjs"
    assert plugin.language == "typescript"
    assert mappings["controller"].endswith("ai_assistant.controller.ts.j2")
    assert outputs["configuration"].endswith("configuration.ts")
    assert enriched["framework_display_name"] == "NestJS"
    assert plugin.get_dependencies() == ["@nestjs/common>=10.0.0"]
    assert "ts-jest>=29.0.0" in plugin.get_dev_dependencies()

    output_dir = tmp_path / "nestjs"
    plugin.pre_generation_hook(output_dir)
    assert (
        output_dir / "src" / "modules" / "free" / "ai" / "ai_assistant" / "ai-assistant"
    ).is_dir()
    plugin.post_generation_hook(output_dir)
