from __future__ import annotations

import os
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest
from _pytest.capture import CaptureFixture
from pytest import MonkeyPatch

from cli import global_cli
from core.config.version import get_version


def _make_project_root(base: Path) -> Path:
    project_root = base / "rapidkit-proj"
    (project_root / ".rapidkit").mkdir(parents=True)
    (project_root / ".rapidkit" / "project.json").write_text("{}", encoding="utf-8")
    (project_root / "pyproject.toml").write_text("[tool.poetry]\nname='demo'\n", encoding="utf-8")
    (project_root / "src").mkdir()
    return project_root


def test_main_without_args_shows_help(
    monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["rapidkit"])

    global_cli.main()

    captured = capsys.readouterr()
    assert "RapidKit Global CLI" in captured.out
    assert "Global Engine Commands" in captured.out


def test_show_help_outside_project_lists_global_first(
    monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    monkeypatch.setattr(global_cli, "_find_project_root", lambda: None)

    global_cli._show_help()

    captured = capsys.readouterr().out
    global_index = captured.index("🏗️  Global Engine Commands (run anywhere):")
    project_index = captured.index("🚀 Project Commands (run within RapidKit projects):")
    assert global_index < project_index


def test_show_help_inside_project_lists_project_first(
    monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    monkeypatch.setattr(global_cli, "_find_project_root", lambda: Path.cwd())

    global_cli._show_help()

    captured = capsys.readouterr().out
    project_index = captured.index("🚀 Project Commands (run within RapidKit projects):")
    global_index = captured.index("🏗️  Global Engine Commands (run anywhere):")
    assert project_index < global_index


def test_project_command_without_project(
    monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["rapidkit", "dev"])
    monkeypatch.setattr(global_cli, "_find_project_root", lambda: None)

    with pytest.raises(SystemExit) as exc:
        global_cli.main()

    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "No RapidKit project found" in captured.out


def test_project_command_delegates_with_poetry(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    project_root = _make_project_root(tmp_path)
    run_calls: list[tuple[list[str], Path, dict[str, str], bool]] = []

    delegated_exit_code = 7

    def _fake_run(cmd: list[str], cwd: Path, env: dict[str, str], check: bool) -> SimpleNamespace:
        run_calls.append((cmd, cwd, env, check))
        return SimpleNamespace(returncode=delegated_exit_code)

    monkeypatch.setattr(sys, "argv", ["rapidkit", "dev"])
    monkeypatch.setattr(global_cli, "_find_project_root", lambda: project_root)
    monkeypatch.setattr("cli.global_cli.subprocess.run", _fake_run)

    with pytest.raises(SystemExit) as exc:
        global_cli.main()

    assert exc.value.code == delegated_exit_code
    assert run_calls, "Expected subprocess.run to be invoked"
    cmd, cwd, env, check = run_calls[0]
    assert cmd[:4] == [sys.executable, "-m", "poetry", "run"]
    assert cmd[4:] == ["dev"]
    assert cwd == project_root
    assert check is False
    pythonpath_entries = env.get("PYTHONPATH", "").split(os.pathsep)
    assert pythonpath_entries[0] == str(project_root / "src")


def test_global_command_invokes_engine_cli(monkeypatch: MonkeyPatch) -> None:
    called = False

    def _fake_cli_main() -> None:
        nonlocal called
        called = True

    dummy_module = ModuleType("cli.main")
    dummy_module.main = _fake_cli_main  # type: ignore[attr-defined]

    monkeypatch.setattr(sys, "argv", ["rapidkit", "create"])
    monkeypatch.setitem(sys.modules, "cli.main", dummy_module)
    if "cli" in sys.modules:
        monkeypatch.setattr(sys.modules["cli"], "main", dummy_module, raising=False)

    global_cli.main()

    assert called


def test_version_flag_outputs_information(
    monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["rapidkit", "--version"])

    global_cli.main()

    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out.strip().splitlines() == [f"RapidKit Version v{get_version()}"]


def test_unknown_command_exits_with_message(
    monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["rapidkit", "unknown"])

    with pytest.raises(SystemExit) as exc:
        global_cli.main()

    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "Unknown command" in captured.out


def test_launch_tui_import_error(monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]) -> None:
    monkeypatch.setitem(sys.modules, "core.tui", ModuleType("core.tui"))
    monkeypatch.setitem(sys.modules, "core.tui.main_tui", ModuleType("core.tui.main_tui"))

    global_cli._launch_tui()

    captured = capsys.readouterr()
    assert "Interactive TUI unavailable" in captured.out
    assert "RapidTUI" in captured.out
