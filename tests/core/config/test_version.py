from __future__ import annotations

import sys
from types import ModuleType

import pytest

from core.config import version as version_module

MIN_VERSION_SEPARATOR_COUNT = 2


def test_check_min_version_allows_equal_or_higher() -> None:
    version_module.check_min_version("1.0.0", "1.0.0")
    version_module.check_min_version("1.0.0", "1.2.0")


def test_check_min_version_raises_for_too_low_version() -> None:
    with pytest.raises(RuntimeError):
        version_module.check_min_version("2.0.0", "1.9.9")


def test_get_version_prefers_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = "9.9.9"

    def fake_metadata(name: str) -> str:
        if name == "rapidkit-core":
            return expected
        raise version_module.metadata.PackageNotFoundError

    monkeypatch.setattr(version_module.metadata, "version", fake_metadata)
    monkeypatch.setattr(
        version_module,
        "_read_module_version",
        lambda *_args, **_kwargs: pytest.fail("should not reach module fallback"),
    )
    monkeypatch.setattr(
        version_module,
        "_read_pyproject_version",
        lambda: pytest.fail("should not reach pyproject fallback"),
    )

    assert version_module.get_version() == expected


def test_get_version_prefers_module_version_when_metadata_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_metadata(_: str) -> str:
        raise version_module.metadata.PackageNotFoundError

    monkeypatch.setattr(version_module.metadata, "version", fail_metadata)

    module_version = "2.3.4"
    monkeypatch.setattr(version_module, "_read_module_version", lambda *_: module_version)
    monkeypatch.setattr(
        version_module,
        "_read_pyproject_version",
        lambda: pytest.fail("should not reach pyproject fallback"),
    )

    assert version_module.get_version() == module_version


def test_get_version_uses_pyproject_as_final_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_metadata(_: str) -> str:
        raise version_module.metadata.PackageNotFoundError

    monkeypatch.setattr(version_module.metadata, "version", fail_metadata)
    monkeypatch.setattr(version_module, "_read_module_version", lambda *_: None)

    pyproject_version = "3.4.5"
    monkeypatch.setattr(version_module, "_read_pyproject_version", lambda: pyproject_version)

    assert version_module.get_version() == pyproject_version


def test_get_version_returns_current_version_when_all_sources_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_metadata(_: str) -> str:
        raise version_module.metadata.PackageNotFoundError

    monkeypatch.setattr(version_module.metadata, "version", fail_metadata)
    monkeypatch.setattr(version_module, "_read_module_version", lambda *_: None)
    monkeypatch.setattr(version_module, "_read_pyproject_version", lambda: None)

    assert version_module.get_version() == version_module.CURRENT_VERSION


def test_get_cli_version_prefers_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = "4.5.6"

    def fake_metadata(name: str) -> str:
        if name == "rapidkit-cli":
            return expected
        raise version_module.metadata.PackageNotFoundError

    monkeypatch.setattr(version_module.metadata, "version", fake_metadata)
    monkeypatch.setattr(
        version_module,
        "_read_module_version",
        lambda *_args, **_kwargs: pytest.fail("should not reach module fallback"),
    )

    assert version_module.get_cli_version() == expected


def test_get_cli_version_prefers_module_over_pyproject(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_metadata(_: str) -> str:
        raise version_module.metadata.PackageNotFoundError

    monkeypatch.setattr(version_module.metadata, "version", fail_metadata)

    cli_module_version = "5.6.7"
    monkeypatch.setattr(version_module, "_read_module_version", lambda *_: cli_module_version)
    monkeypatch.setattr(version_module, "_read_pyproject_version", lambda: "not-used")

    assert version_module.get_cli_version() == cli_module_version


def test_get_cli_version_returns_current_version_when_all_sources_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_metadata(_: str) -> str:
        raise version_module.metadata.PackageNotFoundError

    monkeypatch.setattr(version_module.metadata, "version", fail_metadata)
    monkeypatch.setattr(version_module, "_read_module_version", lambda *_: None)
    monkeypatch.setattr(version_module, "_read_pyproject_version", lambda: None)

    assert version_module.get_cli_version() == version_module.CURRENT_VERSION


def test_read_module_version_returns_first_available(monkeypatch: pytest.MonkeyPatch) -> None:
    module = ModuleType("rapidkit_test_module")
    setattr(module, "__version__", "7.8.9")  # noqa: B010 - test double needs dynamic attribute

    monkeypatch.setitem(sys.modules, "rapidkit_test_module", module)
    try:
        assert version_module._read_module_version("rapidkit_test_module") == "7.8.9"
    finally:
        sys.modules.pop("rapidkit_test_module", None)


def test_read_module_version_skips_missing_and_invalid_entries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class DummyModule(ModuleType):
        def __init__(self) -> None:
            super().__init__("dummy")
            self.__version__ = 0

    monkeypatch.setitem(sys.modules, "dummy_invalid", DummyModule())
    try:
        assert version_module._read_module_version("missing", "dummy_invalid") is None
    finally:
        sys.modules.pop("dummy_invalid", None)


def test_resolve_metadata_version_returns_first_available(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[str] = []

    def fake_metadata(name: str) -> str:
        seen.append(name)
        if name == "pkg-second":
            return "8.8.8"
        raise version_module.metadata.PackageNotFoundError

    monkeypatch.setattr(version_module.metadata, "version", fake_metadata)

    result = version_module._resolve_metadata_version(["pkg-first", "pkg-second", "pkg-third"])

    assert result == "8.8.8"
    assert seen == ["pkg-first", "pkg-second"]


def test_resolve_metadata_version_returns_none_when_all_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(_: str) -> str:
        raise version_module.metadata.PackageNotFoundError

    monkeypatch.setattr(version_module.metadata, "version", fail)

    assert version_module._resolve_metadata_version(["missing-one", "missing-two"]) is None


def test_read_pyproject_version_parses_repo_file() -> None:
    pyproject_version = version_module._read_pyproject_version()

    assert pyproject_version is not None
    assert pyproject_version.count(".") >= MIN_VERSION_SEPARATOR_COUNT
