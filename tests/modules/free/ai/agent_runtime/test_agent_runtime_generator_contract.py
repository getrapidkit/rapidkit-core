from __future__ import annotations

from modules.free.ai.agent_runtime import generate
from modules.free.ai.agent_runtime.frameworks import (
    get_plugin,
    list_available_plugins,
    refresh_plugin_registry,
)


def test_agent_runtime_generator_context_and_vendor_path_contract() -> None:
    config = generate.load_module_config()
    context = generate.build_base_context(config)

    assert generate.infer_vendor_primary_path(config) == generate.VENDOR_RELATIVE
    assert context["module_slug"] == "free/ai/agent_runtime"
    assert context["rapidkit_vendor_relative_path"] == generate.VENDOR_RELATIVE
    assert context["rapidkit_vendor_types_path"] == generate.VENDOR_TYPES_RELATIVE
    assert context["rapidkit_vendor_health_path"] == generate.VENDOR_HEALTH_RELATIVE


def test_agent_runtime_vendor_path_falls_back_for_incomplete_config() -> None:
    assert generate.infer_vendor_primary_path({}) == generate.VENDOR_RELATIVE
    assert (
        generate.infer_vendor_primary_path(
            {
                "generation": {
                    "vendor": {
                        "files": [
                            {
                                "template": "templates/base/not-agent-runtime.py.j2",
                                "relative": "src/ignored.py",
                            }
                        ]
                    }
                }
            }
        )
        == generate.VENDOR_RELATIVE
    )


def test_agent_runtime_builtin_plugin_registry_contract() -> None:
    refresh_plugin_registry(auto_discover=False)

    available = list_available_plugins()

    assert available == {"fastapi": "FastAPI", "nestjs": "NestJS"}
    assert get_plugin("fastapi").language == "python"
    assert get_plugin("nestjs").language == "typescript"
