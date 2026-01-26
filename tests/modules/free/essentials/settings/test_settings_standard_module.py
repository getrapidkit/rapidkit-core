import contextlib
import importlib
import importlib.util
import sys
import types
from pathlib import Path

import pytest

from modules.free.essentials.settings import generate
from modules.free.essentials.settings.frameworks.fastapi import FastAPIPlugin


@pytest.fixture
def fastapi_generation(tmp_path, monkeypatch):
    """Generate the FastAPI settings variant into a temporary directory."""

    pytest.importorskip("fastapi")

    target_dir = tmp_path / "generated"

    def _no_bump(config, **unused):
        if unused:
            next(iter(unused.items()))
        return dict(config), False

    monkeypatch.setattr(generate, "ensure_version_consistency", _no_bump)
    monkeypatch.setattr(generate.sys, "argv", ["generate.py", "fastapi", str(target_dir)])

    generate.main()
    return target_dir


def _import_generated_settings(target_dir: Path, monkeypatch) -> object:
    vendor_root = target_dir / ".rapidkit" / "vendor"
    monkeypatch.setenv("RAPIDKIT_VENDOR_ROOT", str(vendor_root))

    module_name = "modules.free.essentials.settings.settings"
    generated_modules_root = target_dir / "src" / "modules"
    settings_root = generated_modules_root / "free" / "essentials" / "settings"
    settings_module_path = settings_root / "settings.py"

    tracked_names = [
        module_name,
        "modules",
        "src.modules",
        "modules.shared",
        "modules.free",
        "modules.free.essentials",
        "modules.free.essentials.settings",
    ]
    originals = {name: sys.modules.get(name) for name in tracked_names}
    for name in tracked_names:
        sys.modules.pop(name, None)

    assert (settings_module_path).exists()

    def _install_pkg(name: str, path: Path) -> None:
        pkg = types.ModuleType(name)
        pkg.__path__ = [str(path)]  # type: ignore[attr-defined]
        pkg.__package__ = name
        sys.modules[name] = pkg

    # Force the import to resolve strictly from the generated tree to avoid
    # collisions with the repo's own generator package at
    # src/modules/free/essentials/settings.
    _install_pkg("modules", generated_modules_root)
    _install_pkg("modules.free", generated_modules_root / "free")
    _install_pkg("modules.free.essentials", generated_modules_root / "free" / "essentials")
    _install_pkg("modules.free.essentials.settings", settings_root)

    spec = importlib.util.spec_from_file_location(module_name, settings_module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    # Cleanup: importing the generated module can leave behind namespace packages
    # (e.g., src.modules) that pollute later imports in the test run.
    for name in tracked_names:
        sys.modules.pop(name, None)
        original = originals.get(name)
        if original is not None:
            sys.modules[name] = original

    return module


def test_fastapi_generation_rehydrates_basesettings(fastapi_generation, monkeypatch):
    import pydantic
    from pydantic.errors import PydanticImportError
    from pydantic_settings import BaseSettings as PydanticSettingsBase

    with contextlib.suppress(PydanticImportError):
        monkeypatch.delattr(pydantic, "BaseSettings", raising=False)

    module = _import_generated_settings(fastapi_generation, monkeypatch)

    assert module.BaseSettings is PydanticSettingsBase
    assert pydantic.BaseSettings is PydanticSettingsBase

    settings_instance = module.Settings()
    assert hasattr(settings_instance, "PROJECT_NAME")


def test_infer_vendor_settings_path_prefers_settings_template():
    config = {
        "generation": {
            "vendor": {
                "files": [
                    {"template": "something_else.py.j2", "relative": "ignored"},
                    {"template": "whatever/settings.py.j2", "relative": "expected"},
                ]
            }
        }
    }

    inferred = generate.infer_vendor_settings_path(config)
    assert inferred == "expected"


def test_infer_vendor_settings_path_defaults_when_missing():
    assert (
        generate.infer_vendor_settings_path({})
        == "src/modules/free/essentials/settings/settings.py"
    )


def test_fastapi_plugin_validates_missing_fastapi(monkeypatch):
    plugin = FastAPIPlugin()

    monkeypatch.delitem(sys.modules, "fastapi", raising=False)

    import importlib.util as importlib_util

    monkeypatch.setattr(importlib_util, "find_spec", lambda _: None)

    errors = plugin.validate_requirements()
    assert any("FastAPI is not installed" in err for err in errors)


def test_fastapi_plugin_detects_outdated_fastapi(monkeypatch):
    plugin = FastAPIPlugin()

    class _Stub:
        __version__ = "0.118.0"

    monkeypatch.setitem(sys.modules, "fastapi", _Stub())

    errors = plugin.validate_requirements()
    assert any("too old" in err for err in errors)
