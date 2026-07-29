import sys
from importlib import import_module
from pathlib import Path
from typing import Any, Mapping

import pytest

from modules.free.billing.usage_billing import generate


def test_usage_billing_generator_entrypoint() -> None:
    """Ensure the module generator can be imported without crashing."""

    generator_module = import_module("modules.free.billing.usage_billing.generate")
    assert hasattr(generator_module, "main"), "Expected a main() entrypoint on the generator module"


def test_usage_billing_generator_error_preserves_exit_context() -> None:
    error = generate.GeneratorError("generation failed", exit_code=7)

    assert error.exit_code == 7
    assert error.context["exit_code"] == 7


def test_usage_billing_vendor_path_uses_matching_manifest_entry() -> None:
    config = {
        "generation": {
            "vendor": {
                "files": [
                    {"template": "ignored.txt.j2", "relative": "ignored.txt"},
                    {
                        "template": "templates/usage_billing.py.j2",
                        "relative": "custom/usage_billing.py",
                    },
                ]
            }
        }
    }

    assert generate.infer_vendor_primary_path(config) == "custom/usage_billing.py"
    assert generate.infer_vendor_primary_path({}) == generate.VENDOR_RELATIVE


def test_usage_billing_module_level_generation_wrappers(tmp_path: Path) -> None:
    config = generate.load_module_config()
    context = generate.build_base_context(config)
    renderer = generate.UsageBillingModuleGenerator().create_renderer()

    generate.generate_vendor_files(config, tmp_path, renderer, context)
    generate.generate_variant_files("fastapi", tmp_path, renderer, context)

    assert context["module_slug"] == generate.MODULE_SLUG
    assert (
        tmp_path / "src" / "modules" / "free" / "billing" / "usage_billing" / "usage_billing.py"
    ).exists()


class _FakeGenerator:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.calls: list[tuple[str, object]] = []

    def load_module_config(self) -> dict[str, str]:
        if self.error is not None:
            raise self.error
        return {"name": "usage_billing", "version": "0.1.0"}

    def build_base_context(self, config: Mapping[str, Any]) -> dict[str, str]:
        self.calls.append(("context", dict(config)))
        return {"module_name": str(config["name"])}

    def create_renderer(self) -> object:
        return object()

    def generate_vendor_files(
        self,
        _config: Mapping[str, Any],
        target_dir: Path,
        _renderer: object,
        _context: Mapping[str, Any],
    ) -> None:
        self.calls.append(("vendor", target_dir))

    def generate_variant_files(
        self,
        variant_name: str,
        _target_dir: Path,
        _renderer: object,
        _context: Mapping[str, Any],
    ) -> None:
        self.calls.append(("variant", variant_name))


def test_usage_billing_main_runs_generation_pipeline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = _FakeGenerator()
    monkeypatch.setattr(generate, "UsageBillingModuleGenerator", lambda: fake)
    monkeypatch.setattr(
        generate,
        "ensure_version_consistency",
        lambda config, *, module_root: ({**config, "version": "0.1.1"}, True),
    )
    monkeypatch.setattr(sys, "argv", ["generate", "fastapi", str(tmp_path)])

    generate.main()

    assert ("variant", "fastapi") in fake.calls
    assert ("vendor", tmp_path.resolve()) in fake.calls
    assert "Auto bumped usage_billing module version to 0.1.1" in capsys.readouterr().out


def test_usage_billing_main_rejects_incomplete_arguments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["generate"])

    with pytest.raises(generate.GeneratorError) as raised:
        generate.main()

    assert raised.value.exit_code == 2
    assert raised.value.context["provided_args"] == []
    assert raised.value.context["expected_arg_count"] == 2


def test_usage_billing_main_reports_generator_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    error = generate.GeneratorError("render failed", exit_code=4, context={"variant": "fastapi"})
    monkeypatch.setattr(generate, "UsageBillingModuleGenerator", lambda: _FakeGenerator(error))
    monkeypatch.setattr(
        generate, "format_missing_dependencies", lambda _missing: "Install renderer"
    )
    monkeypatch.setattr(sys, "argv", ["generate", "fastapi", str(tmp_path)])

    with pytest.raises(SystemExit) as raised:
        generate.main()

    output = capsys.readouterr().out
    assert raised.value.code == 4
    assert "Generator Error: render failed" in output
    assert "variant: fastapi" in output
    assert "Install renderer" in output


def test_usage_billing_main_reports_unexpected_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        generate,
        "UsageBillingModuleGenerator",
        lambda: _FakeGenerator(RuntimeError("unexpected render failure")),
    )
    monkeypatch.setattr(sys, "argv", ["generate", "fastapi", str(tmp_path)])

    with pytest.raises(SystemExit) as raised:
        generate.main()

    output = capsys.readouterr().out
    assert raised.value.code == 1
    assert "Generator failed with an unexpected error" in output
    assert "unexpected render failure" in output
    assert "rapidkit modules doctor usage_billing" in output
