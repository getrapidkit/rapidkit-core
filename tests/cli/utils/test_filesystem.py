from __future__ import annotations

from pathlib import Path

from pytest import MonkeyPatch

from cli.utils.filesystem import (
    create_file,
    find_main_py,
    find_project_root,
    resolve_project_path,
)


def test_find_main_py_prioritises_first_match(tmp_path: Path) -> None:
    project = tmp_path
    (project / "app").mkdir()
    (project / "app" / "main.py").write_text("print('app')", encoding="utf-8")
    (project / "main.py").write_text("print('root')", encoding="utf-8")

    result = find_main_py(project)
    assert result == project / "main.py"


def test_find_main_py_uses_base_module(tmp_path: Path) -> None:
    project = tmp_path
    target = project / "custom" / "main.py"
    target.parent.mkdir(parents=True)
    target.write_text("print('custom')", encoding="utf-8")

    result = find_main_py(project, base_module="custom")

    assert result == target


def test_create_file_creates_parent_directories(tmp_path: Path) -> None:
    target = tmp_path / "src" / "pkg" / "module.py"
    create_file(target, "print('hi')")
    assert target.read_text(encoding="utf-8") == "print('hi')"


def test_find_project_root_with_target(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "boilerplates" / "demo").mkdir(parents=True)
    root = find_project_root("demo")
    assert root == (tmp_path / "boilerplates" / "demo").resolve()


def test_find_project_root_detects_markers(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    project = tmp_path / "demo"
    (project / ".rapidkit").mkdir(parents=True)
    monkeypatch.chdir(project)

    found = find_project_root()
    assert found == project


def test_find_project_root_legacy_registry(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    project = tmp_path / "legacy"
    project.mkdir()
    (project / "registry.json").write_text("{}", encoding="utf-8")
    monkeypatch.chdir(project)

    found = find_project_root()
    assert found == project


def test_find_main_py_returns_none_when_missing(tmp_path: Path) -> None:
    assert find_main_py(tmp_path) is None


def test_find_project_root_lists_boilerplates(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    (workspace / "boilerplates" / "a").mkdir(parents=True)
    (workspace / "boilerplates" / "b").mkdir(parents=True)
    monkeypatch.chdir(workspace)

    result = find_project_root("boilerplates")

    assert result == (workspace / "boilerplates" / "a").resolve()


def test_find_project_root_handles_nested_boilerplates(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    workspace = tmp_path / "ws"
    target = workspace / "boilerplates" / "nested" / "boilerplates"
    (target / "inner").mkdir(parents=True)
    monkeypatch.chdir(workspace)

    result = find_project_root("nested/boilerplates")

    assert result == (target / "inner").resolve()


def test_find_project_root_returns_none_when_not_found(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    monkeypatch.chdir(workspace)

    assert find_project_root("missing") is None


def test_find_project_root_prefers_rapidkit_over_nested_snippet(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    project = tmp_path / "demo"
    nested = project / "src"
    (project / ".rapidkit").mkdir(parents=True)
    nested.mkdir(parents=True)
    (nested / "snippet_registry.json").write_text("{}", encoding="utf-8")

    monkeypatch.chdir(nested)

    found = find_project_root()

    assert found == project


def test_resolve_project_path_deduplicates_root_prefix(tmp_path: Path) -> None:
    project = tmp_path
    target = resolve_project_path(project, "src", "src/config/settings.ts")

    assert target == project / "src" / "config" / "settings.ts"


def test_resolve_project_path_applies_root_when_missing(tmp_path: Path) -> None:
    project = tmp_path
    target = resolve_project_path(project, "src", "routers/settings.py")

    assert target == project / "src" / "routers" / "settings.py"
