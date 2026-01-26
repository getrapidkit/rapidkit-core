from importlib import import_module

import pytest

from modules.free.ai.ai_assistant import generate

USAGE_EXIT_CODE = 2
USAGE_EXPECTED_ARGS = 2
GENERATOR_FAILURE_EXIT_CODE = 1


def test_ai_assistant_generator_entrypoint() -> None:
    """Ensure the module generator can be imported without crashing."""

    generator_module = import_module("modules.free.ai.ai_assistant.generate")
    assert hasattr(generator_module, "main"), "Expected a main() entrypoint on the generator module"


def test_infer_vendor_primary_path_uses_configured_entry() -> None:
    custom_relative = "custom/path/ai_assistant.py"
    config = {
        "generation": {
            "vendor": {
                "files": [
                    {
                        "template": f"templates/base/{generate.MODULE_NAME}.py.j2",
                        "relative": custom_relative,
                    }
                ]
            }
        }
    }

    resolved = generate.infer_vendor_primary_path(config)

    assert resolved == custom_relative


def test_build_base_context_includes_expected_values() -> None:
    config = {"name": "demo_assistant", "version": "9.9.9"}

    context = generate.build_base_context(config)

    assert context["module_name"] == "demo_assistant"
    assert context["rapidkit_vendor_version"] == "9.9.9"
    assert context["rapidkit_vendor_relative_path"] == generate.VENDOR_RELATIVE
    assert "runtime-facade" in context["enabled_features"]


def test_main_requires_expected_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(generate.sys, "argv", ["rapidkit-ai-assistant"])

    with pytest.raises(generate.GeneratorError) as excinfo:
        generate.main()

    assert excinfo.value.exit_code == USAGE_EXIT_CODE
    assert excinfo.value.context["expected_arg_count"] == USAGE_EXPECTED_ARGS


def test_main_handles_generator_error(monkeypatch: pytest.MonkeyPatch, tmp_path, capsys) -> None:
    class DummyGenerator:
        def __init__(self) -> None:
            pass

        def load_module_config(self):
            return {"name": generate.MODULE_NAME, "version": "0.1.0"}

        def build_base_context(self, config):
            return {
                "module_name": config["name"],
                "rapidkit_vendor_version": config["version"],
            }

        def create_renderer(self):  # pragma: no cover - simple stub
            class _Renderer:
                pass

            return _Renderer()

        def generate_vendor_files(self, *args, **kwargs):
            raise generate.GeneratorError("boom", context={"detail": "info"})

        def generate_variant_files(self, *args, **kwargs):  # pragma: no cover - not reached
            raise AssertionError("variant generation should not execute in this test")

    monkeypatch.setattr(generate, "AiAssistantModuleGenerator", DummyGenerator)

    def _ensure_version_update(config, **_):  # pragma: no cover - stub signature only
        return ({**config, "version": "0.1.1"}, True)

    monkeypatch.setattr(generate, "ensure_version_consistency", _ensure_version_update)
    monkeypatch.setattr(generate, "format_missing_dependencies", lambda _: "Install extras")
    monkeypatch.setattr(generate.sys, "argv", ["rapidkit-ai-assistant", "fastapi", str(tmp_path)])

    with pytest.raises(SystemExit) as excinfo:
        generate.main()

    assert excinfo.value.code == GENERATOR_FAILURE_EXIT_CODE

    captured = capsys.readouterr().out
    assert "Auto bumped ai_assistant module version to 0.1.1" in captured
    assert "❌ Generator Error: boom" in captured
    assert "detail: info" in captured
    assert "Install extras" in captured


def test_main_handles_unexpected_runtime_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys
) -> None:
    class CrashGenerator:
        def __init__(self) -> None:
            pass

        def load_module_config(self):
            return {"name": generate.MODULE_NAME, "version": "0.1.0"}

        def build_base_context(self, config):
            return {"module_name": config["name"]}

        def create_renderer(self):  # pragma: no cover - simple stub
            class _Renderer:
                pass

            return _Renderer()

        def generate_vendor_files(self, *args, **kwargs):
            raise RuntimeError("simulated crash")

        def generate_variant_files(self, *args, **kwargs):  # pragma: no cover - not reached
            raise AssertionError("variant generation should not run when vendor fails")

    monkeypatch.setattr(generate, "AiAssistantModuleGenerator", CrashGenerator)

    def _ensure_version_passthrough(config, **_):
        return (config, False)

    monkeypatch.setattr(generate, "ensure_version_consistency", _ensure_version_passthrough)
    monkeypatch.setattr(generate.sys, "argv", ["rapidkit-ai-assistant", "fastapi", str(tmp_path)])

    with pytest.raises(SystemExit) as excinfo:
        generate.main()

    assert excinfo.value.code == GENERATOR_FAILURE_EXIT_CODE

    captured = capsys.readouterr().out
    assert "Generator failed with an unexpected error" in captured
    assert "RuntimeError: simulated crash" in captured
