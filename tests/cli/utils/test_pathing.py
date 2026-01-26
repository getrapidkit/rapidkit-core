import pathlib
import types
from typing import Callable, Iterator

import pytest

from cli.utils import pathing


@pytest.fixture(autouse=True)
def clear_pathing_caches() -> Iterator[Callable[[], None]]:
    def _clear() -> None:
        for name in (
            "resolve_repo_root",
            "resolve_src_root",
            "resolve_modules_path",
            "resolve_registry_path",
        ):
            func = getattr(pathing, name)
            cache_clear = getattr(func, "cache_clear", None)
            if cache_clear is not None:
                cache_clear()

    _clear()
    yield _clear
    _clear()


def test_package_dir_returns_none_when_import_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_import_error(_: str) -> None:
        raise ImportError("boom")

    monkeypatch.setattr(pathing.importlib, "import_module", raise_import_error)

    assert pathing._package_dir("missing") is None


def test_package_dir_returns_none_without_file(monkeypatch: pytest.MonkeyPatch) -> None:
    module = types.SimpleNamespace()
    monkeypatch.setattr(pathing.importlib, "import_module", lambda _: module)

    assert pathing._package_dir("module_without_file") is None


def test_package_dir_returns_parent_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    module_file = tmp_path / "pkg" / "__init__.py"
    module_file.parent.mkdir(parents=True)
    module_file.write_text("", encoding="utf-8")
    module = types.SimpleNamespace(__file__=module_file)
    monkeypatch.setattr(pathing.importlib, "import_module", lambda _: module)

    assert pathing._package_dir("modules") == module_file.parent


def test_resolve_repo_root_prefers_src_modules(tmp_path: pathlib.Path) -> None:
    repo = tmp_path / "repo"
    anchor = repo / "src" / "cli" / "utils" / "pathing.py"
    anchor.parent.mkdir(parents=True)
    modules_dir = repo / "src" / "modules"
    modules_dir.mkdir(parents=True)
    anchor.write_text("", encoding="utf-8")

    result = pathing.resolve_repo_root(anchor=anchor)

    assert result == modules_dir.parent


def test_resolve_repo_root_accepts_modules_dir(tmp_path: pathlib.Path) -> None:
    repo = tmp_path / "repo"
    anchor = repo / "packages" / "example.py"
    anchor.parent.mkdir(parents=True)
    (repo / "modules").mkdir(parents=True)
    anchor.write_text("", encoding="utf-8")

    result = pathing.resolve_repo_root(anchor=anchor)

    assert result == repo


def test_resolve_repo_root_uses_installed_modules(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base = tmp_path / "site-packages"
    modules_dir = base / "modules"
    modules_dir.mkdir(parents=True)
    anchor = tmp_path / "random" / "anchor.py"
    anchor.parent.mkdir(parents=True)
    anchor.write_text("", encoding="utf-8")

    def fake_package_dir(name: str) -> pathlib.Path | None:
        return modules_dir if name == "modules" else None

    monkeypatch.setattr(pathing, "_package_dir", fake_package_dir)

    result = pathing.resolve_repo_root(anchor=anchor)

    assert result == base


def test_resolve_repo_root_falls_back_to_cli_package(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base = tmp_path / "alt-site-packages"
    cli_dir = base / "cli"
    cli_dir.mkdir(parents=True)
    anchor = tmp_path / "another" / "anchor.py"
    anchor.parent.mkdir(parents=True)
    anchor.write_text("", encoding="utf-8")

    def fake_package_dir(name: str) -> pathlib.Path | None:
        if name == "cli":
            return cli_dir
        return None

    monkeypatch.setattr(pathing, "_package_dir", fake_package_dir)

    result = pathing.resolve_repo_root(anchor=anchor)

    assert result == base


def test_resolve_repo_root_handles_minimal_tree(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    anchor = tmp_path / "grand" / "parent" / "child" / "anchor.py"
    anchor.parent.mkdir(parents=True)
    anchor.write_text("", encoding="utf-8")

    monkeypatch.setattr(pathing, "_package_dir", lambda *_: None)

    result = pathing.resolve_repo_root(anchor=anchor)

    assert result == anchor.parents[2]


def test_resolve_src_root_prefers_src_directory(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)

    monkeypatch.setattr(pathing, "resolve_repo_root", lambda: repo)

    result = pathing.resolve_src_root()

    assert result == repo / "src"


def test_resolve_src_root_falls_back_to_repo_root(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)

    monkeypatch.setattr(pathing, "resolve_repo_root", lambda: repo)

    result = pathing.resolve_src_root()

    assert result == repo


def test_resolve_modules_path_prefers_src_package(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    modules_dir = repo / "src" / "modules"
    modules_dir.mkdir(parents=True)

    monkeypatch.setattr(pathing, "resolve_repo_root", lambda: repo)
    monkeypatch.setattr(pathing, "_package_dir", lambda *_: None)

    result = pathing.resolve_modules_path()

    assert result == modules_dir


def test_resolve_modules_path_supports_flat_layout(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    modules_dir = repo / "modules"
    modules_dir.mkdir(parents=True)

    monkeypatch.setattr(pathing, "resolve_repo_root", lambda: repo)
    monkeypatch.setattr(pathing, "_package_dir", lambda *_: None)

    result = pathing.resolve_modules_path()

    assert result == modules_dir


def test_resolve_modules_path_uses_installed_package(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    site_modules = tmp_path / "site-packages" / "modules"
    site_modules.mkdir(parents=True)

    monkeypatch.setattr(pathing, "resolve_repo_root", lambda: repo)

    def fake_package_dir(name: str) -> pathlib.Path | None:
        return site_modules if name == "modules" else None

    monkeypatch.setattr(pathing, "_package_dir", fake_package_dir)

    result = pathing.resolve_modules_path()

    assert result == site_modules


def test_resolve_modules_path_raises_when_missing(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)

    monkeypatch.setattr(pathing, "resolve_repo_root", lambda: repo)
    monkeypatch.setattr(pathing, "_package_dir", lambda *_: None)

    with pytest.raises(RuntimeError):
        pathing.resolve_modules_path()


def test_resolve_registry_path_respects_repo_root(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)

    monkeypatch.setattr(pathing, "resolve_repo_root", lambda: repo)

    result = pathing.resolve_registry_path()

    assert result == repo / "registry.json"
