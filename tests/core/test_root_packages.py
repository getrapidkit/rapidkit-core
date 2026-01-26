from __future__ import annotations

import importlib
import sys
import types

import pytest

import cli
import src
from cli import __getattr__ as cli_getattr


def test_src_get_supreme_info_contains_expected_keys() -> None:
    info = src.get_supreme_info()

    assert info["version"] == src.__version__
    assert set(info["features"]) == set(src.SUPREME_FEATURES)
    assert info["quantum_ready"] is True
    assert info["ai_integrated"] is True
    assert info["cosmic_scale"] is True


def test_cli_getattr_imports_global_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    stub_module = types.ModuleType("cli.global_cli")
    monkeypatch.setitem(sys.modules, "cli.global_cli", stub_module)

    try:
        imported = cli_getattr("global_cli")
        assert imported is stub_module
    finally:
        sys.modules.pop("cli.global_cli", None)


def test_cli_getattr_falls_back_to_main(monkeypatch: pytest.MonkeyPatch) -> None:
    stub_main = types.ModuleType("cli.main")
    monkeypatch.setitem(sys.modules, "cli.main", stub_main)
    call_log: list[str] = []

    def fake_import(name: str, package: str | None = None) -> types.ModuleType:
        _ = package
        call_log.append(name)
        if name == ".global_cli":
            raise ModuleNotFoundError
        assert name == ".main"
        return stub_main

    monkeypatch.setattr(importlib, "import_module", fake_import)

    imported = cli_getattr("global_cli")

    assert imported is stub_main
    assert call_log == [".global_cli", ".main"]


def test_cli_getattr_raises_for_unknown_attribute() -> None:
    with pytest.raises(AttributeError):
        cli_getattr("unknown")


def test_cli_dir_includes_global_cli() -> None:
    entries = cli.__dir__()

    assert "global_cli" in entries
