import sys
from importlib import import_module
from pathlib import Path

import pytest

from modules.free.communication.webhook_platform import generate


def test_webhook_platform_generator_entrypoint() -> None:
    """Ensure the module generator can be imported without crashing."""

    generator_module = import_module("modules.free.communication.webhook_platform.generate")
    assert hasattr(generator_module, "main"), "Expected a main() entrypoint on the generator module"


def test_webhook_platform_infers_vendor_primary_path_from_config() -> None:
    config = {
        "generation": {
            "vendor": {
                "files": [
                    {
                        "template": "base/webhook_platform_types.py.j2",
                        "relative": "src/types.py",
                    },
                    {
                        "template": "base/webhook_platform.py.j2",
                        "relative": "src/custom/webhook_platform.py",
                    },
                ]
            }
        }
    }

    assert generate.infer_vendor_primary_path(config) == "src/custom/webhook_platform.py"


def test_webhook_platform_infers_default_vendor_primary_path() -> None:
    assert generate.infer_vendor_primary_path({}) == generate.VENDOR_RELATIVE


def test_webhook_platform_generator_error_preserves_exit_code() -> None:
    error = generate.GeneratorError("bad input", exit_code=7)

    assert error.exit_code == 7
    assert error.context["exit_code"] == 7


def test_webhook_platform_module_level_wrappers(monkeypatch, tmp_path: Path) -> None:
    calls: list[tuple[str, object]] = []

    class FakeGenerator:
        def load_module_config(self) -> dict[str, str]:
            calls.append(("load", None))
            return {"name": "webhook_platform"}

        def build_base_context(self, config: dict[str, str]) -> dict[str, str]:
            calls.append(("context", config["name"]))
            return {"module_name": config["name"]}

        def generate_vendor_files(self, config, target_dir, renderer, context) -> None:  # type: ignore[no-untyped-def]
            calls.append(("vendor", target_dir))

        def generate_variant_files(self, variant_name, target_dir, renderer, context) -> None:  # type: ignore[no-untyped-def]
            calls.append(("variant", variant_name))

    monkeypatch.setattr(generate, "_create_generator", FakeGenerator)

    config = generate.load_module_config()
    context = generate.build_base_context(config)
    generate.generate_vendor_files(config, tmp_path, object(), context)
    generate.generate_variant_files("fastapi", tmp_path, object(), context)

    assert calls == [
        ("load", None),
        ("context", "webhook_platform"),
        ("vendor", tmp_path),
        ("variant", "fastapi"),
    ]


def test_webhook_platform_main_rejects_missing_arguments(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(sys, "argv", ["generate.py"])

    with pytest.raises(generate.GeneratorError) as exc_info:
        generate.main()

    assert exc_info.value.exit_code == 2
    assert "Available frameworks" in exc_info.value.message


def test_webhook_platform_main_generates_fastapi_project(
    monkeypatch,
    tmp_path: Path,
) -> None:
    target_dir = tmp_path / "generated"
    monkeypatch.setattr(sys, "argv", ["generate.py", "fastapi", str(target_dir)])

    generate.main()

    assert (
        target_dir / "src/modules/free/communication/webhook_platform/webhook_platform.py"
    ).exists()
    assert (
        target_dir
        / "src/modules/free/communication/webhook_platform/routers/communication/webhook_platform.py"
    ).exists()
