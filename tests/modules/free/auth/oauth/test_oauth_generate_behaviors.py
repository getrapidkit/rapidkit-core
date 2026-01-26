import types
from pathlib import Path

import pytest

from modules.free.auth.oauth import generate


class DummyRenderer:
    def __init__(self, content: str = "rendered", capture: dict | None = None) -> None:
        self._content = content
        self._capture = capture

    def render(self, template_path: Path, context: dict) -> str:
        if self._capture is not None:
            self._capture["template"] = template_path
            self._capture["context"] = dict(context)
        return self._content


def _make_template(module_root: Path, name: str) -> Path:
    template_path = module_root / name
    template_path.parent.mkdir(parents=True, exist_ok=True)
    template_path.write_text("placeholder", encoding=generate.DEFAULT_ENCODING)
    return template_path


def test_generate_vendor_files_creates_expected_output(tmp_path, monkeypatch):
    module_root = tmp_path / "module"
    module_root.mkdir()
    _make_template(module_root, "vendor.py.j2")
    monkeypatch.setattr(generate, "MODULE_ROOT", module_root)

    config = {
        "generation": {
            "vendor": {
                "root": ".rapidkit/vendor",
                "files": [
                    {
                        "template": "vendor.py.j2",
                        "relative": "src/modules/free/auth/oauth/oauth.py",
                        "context": {"extra": "value"},
                    }
                ],
            }
        }
    }
    context = {
        "rapidkit_vendor_module": "vendor",
        "rapidkit_vendor_version": "1.2.3",
    }

    target_dir = tmp_path / "target"
    generate.generate_vendor_files(config, target_dir, DummyRenderer("content"), context)

    output_file = target_dir / ".rapidkit/vendor/vendor/1.2.3/src/modules/free/auth/oauth/oauth.py"
    assert output_file.read_text(encoding=generate.DEFAULT_ENCODING) == "content"


def test_generate_vendor_files_missing_relative_raises(tmp_path, monkeypatch):
    module_root = tmp_path / "module"
    module_root.mkdir()
    _make_template(module_root, "vendor.py.j2")
    monkeypatch.setattr(generate, "MODULE_ROOT", module_root)

    config = {
        "generation": {
            "vendor": {
                "files": [
                    {
                        "template": "vendor.py.j2",
                    }
                ],
            }
        }
    }
    context = {
        "rapidkit_vendor_module": "vendor",
        "rapidkit_vendor_version": "1.2.3",
    }

    with pytest.raises(generate.GeneratorError) as exc:
        generate.generate_vendor_files(config, tmp_path, DummyRenderer(), context)
    assert "relative" in exc.value.message


def test_generate_variant_files_creates_files(tmp_path, monkeypatch):
    module_root = tmp_path / "module"
    module_root.mkdir()
    _make_template(module_root, "variants/fastapi.py.j2")
    monkeypatch.setattr(generate, "MODULE_ROOT", module_root)

    config = {
        "generation": {
            "variants": {
                "fastapi": {
                    "root": ".",
                    "context": {"base": "value"},
                    "files": [
                        {
                            "template": "variants/fastapi.py.j2",
                            "output": "src/modules/free/auth/oauth/oauth.py",
                            "context": {"extra": "info"},
                        }
                    ],
                }
            }
        }
    }
    base_context = generate.build_base_context({"name": "oauth", "version": "9.9.9"})

    capture: dict = {}
    target_dir = tmp_path / "target"
    generate.generate_variant_files(
        config,
        "fastapi",
        target_dir,
        DummyRenderer("variant", capture),
        base_context,
    )

    output_file = target_dir / "src/modules/free/auth/oauth/oauth.py"
    assert output_file.read_text(encoding=generate.DEFAULT_ENCODING) == "variant"
    assert capture["template"].name == "fastapi.py.j2"
    assert capture["context"]["base"] == "value"
    assert capture["context"]["extra"] == "info"
    assert capture["context"]["module_title"] == generate.MODULE_TITLE


def test_generate_variant_files_missing_variant(tmp_path):
    config = {"generation": {"variants": {"fastapi": {}}}}
    with pytest.raises(generate.GeneratorError) as exc:
        generate.generate_variant_files(
            config,
            "graphql",
            tmp_path,
            DummyRenderer(),
            {},
        )
    assert "available" in exc.value.message


def test_generate_variant_files_missing_template_raises(tmp_path, monkeypatch):
    module_root = tmp_path / "module"
    module_root.mkdir()
    monkeypatch.setattr(generate, "MODULE_ROOT", module_root)

    config = {
        "generation": {
            "variants": {
                "fastapi": {
                    "files": [
                        {
                            "template": "variants/fastapi.py.j2",
                            "output": "src/modules/free/auth/oauth/oauth.py",
                        }
                    ],
                }
            }
        }
    }

    with pytest.raises(generate.GeneratorError) as exc:
        generate.generate_variant_files(
            config,
            "fastapi",
            tmp_path,
            DummyRenderer(),
            {},
        )
    assert "Variant template" in exc.value.message


def test_template_renderer_requires_jinja(monkeypatch):
    monkeypatch.setattr(generate, "JinjaEnvironment", None)
    monkeypatch.setattr(generate, "FileSystemLoader", None)
    monkeypatch.setattr(generate, "StrictUndefined", None)
    renderer = generate.TemplateRenderer()

    with pytest.raises(generate.GeneratorError) as exc:
        renderer.render(Path("any"), {})
    assert "jinja2" in exc.value.message


def test_build_base_context_uses_defaults():
    config = {
        "name": "custom",
        "version": "1.5.0",
        "defaults": {"flag": True},
    }
    context = generate.build_base_context(config)
    assert context[generate.DEFAULTS_KEY] == {"flag": True}
    assert context["module_title"] == generate.MODULE_TITLE


def test_format_missing_dependencies_lists_entries():
    message = generate._format_missing_dependencies({"jinja2": "Install"})
    assert "Missing optional dependencies" in message
    assert "jinja2" in message


def test_main_requires_variant_and_target(monkeypatch):
    fake_sys = types.SimpleNamespace(
        argv=["prog"], exit=lambda code: (_ for _ in ()).throw(SystemExit(code))
    )
    monkeypatch.setattr(generate, "sys", fake_sys)

    with pytest.raises(generate.GeneratorError) as exc:
        generate.main()
    assert "Usage" in exc.value.message


def test_main_handles_generator_error(monkeypatch, capsys):
    fake_sys = types.SimpleNamespace(
        argv=["prog", "fastapi", "target"],
        exit=lambda code: (_ for _ in ()).throw(SystemExit(code)),
    )
    monkeypatch.setattr(generate, "sys", fake_sys)

    monkeypatch.setattr(generate, "load_module_config", lambda: {})

    def _mock_ensure_version_consistency(config, module_root):
        del module_root
        return config, False

    monkeypatch.setattr(generate, "ensure_version_consistency", _mock_ensure_version_consistency)
    monkeypatch.setattr(generate, "TemplateRenderer", lambda: DummyRenderer())

    def _noop_generate_vendor_files(config, target_dir, renderer, context):
        del config, target_dir, renderer, context

    monkeypatch.setattr(generate, "generate_vendor_files", _noop_generate_vendor_files)

    expected_exit_code = 5

    def _raise_generator_error(config, variant_name, target_dir, renderer, context):
        del config, variant_name, target_dir, renderer, context
        raise generate.GeneratorError("boom", exit_code=expected_exit_code)

    monkeypatch.setattr(generate, "generate_variant_files", _raise_generator_error)

    with pytest.raises(SystemExit) as exc:
        generate.main()
    assert exc.value.code == expected_exit_code

    captured = capsys.readouterr()
    assert "boom" in captured.out
    assert captured.err == ""
