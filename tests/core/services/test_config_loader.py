import textwrap
from pathlib import Path
from typing import Callable, List, Tuple

import pytest

from core.services import config_loader


def _capture_messages(monkeypatch: pytest.MonkeyPatch) -> List[Tuple[str, str]]:
    messages: List[Tuple[str, str]] = []

    def _make_recorder(level: str) -> Callable[[str], None]:
        def _record(message: str) -> None:
            messages.append((level, message))

        return _record

    monkeypatch.setattr(config_loader, "print_info", _make_recorder("info"))
    monkeypatch.setattr(config_loader, "print_warning", _make_recorder("warning"))
    monkeypatch.setattr(config_loader, "print_error", _make_recorder("error"))
    return messages


def test_load_module_config_merges_files_and_applies_overrides(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    modules_root = tmp_path / "modules"
    config_dir = modules_root / "demo" / "config"
    override_dir = config_dir / "overrides"
    override_dir.mkdir(parents=True)

    (config_dir / "base.yaml").write_text(
        textwrap.dedent(
            """
            name: Demo Module
            metadata:
              base: true
            """
        ).strip()
    )
    (config_dir / "features.yaml").write_text(
        textwrap.dedent(
            """
            metadata:
              feature_flag: true
            """
        ).strip()
    )
    (config_dir / "profiles.yaml").write_text(
        textwrap.dedent(
            """
            profiles:
              default: true
            """
        ).strip()
    )
    (override_dir / "fastapi.yaml").write_text(
        textwrap.dedent(
            """
            metadata:
              override: fastapi
            """
        ).strip()
    )
    (modules_root / "demo" / "module.yaml").write_text("version: 0.1.0\n")

    monkeypatch.setattr(config_loader, "MODULES_PATH", modules_root)
    monkeypatch.setenv("RAPIDKIT_DEBUG", "true")
    messages = _capture_messages(monkeypatch)

    result = config_loader.load_module_config("demo", profile="fastapi/basic")

    assert result["name"] == "Demo Module"
    assert result["version"] == "0.1.0"
    assert result["metadata"] == {
        "base": True,
        "feature_flag": True,
        "override": "fastapi",
    }
    assert result["profiles"] == {"default": True}
    override_messages = [msg for level, msg in messages if level == "info"]
    assert any("Loaded override" in message for message in override_messages)


def test_load_module_config_missing_critical_file_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    modules_root = tmp_path / "modules"
    config_dir = modules_root / "demo" / "config"
    config_dir.mkdir(parents=True)

    (config_dir / "profiles.yaml").write_text("profiles: {}\n")

    monkeypatch.setattr(config_loader, "MODULES_PATH", modules_root)
    monkeypatch.delenv("RAPIDKIT_DEBUG", raising=False)
    messages = _capture_messages(monkeypatch)

    with pytest.raises(FileNotFoundError):
        config_loader.load_module_config("demo")

    error_messages = [msg for level, msg in messages if level == "error"]
    assert any("Critical config file not found" in message for message in error_messages)


def test_load_module_config_missing_required_fields_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    modules_root = tmp_path / "modules"
    config_dir = modules_root / "demo" / "config"
    config_dir.mkdir(parents=True)

    (config_dir / "base.yaml").write_text(
        textwrap.dedent(
            """
            version: 1.2.3
            """
        ).strip()
    )

    monkeypatch.setattr(config_loader, "MODULES_PATH", modules_root)
    monkeypatch.delenv("RAPIDKIT_DEBUG", raising=False)
    messages = _capture_messages(monkeypatch)

    with pytest.raises(ValueError):
        config_loader.load_module_config("demo")

    error_messages = [msg for level, msg in messages if level == "error"]
    assert any("Critical field 'name'" in message for message in error_messages)


def test_load_module_config_infers_feature_profiles_and_slug(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    modules_root = tmp_path / "modules"
    config_dir = modules_root / "demo" / "config"
    config_dir.mkdir(parents=True)

    (config_dir / "base.yaml").write_text(
        textwrap.dedent(
            """
            name: Demo Module
            description: Demo
            profiles:
              fastapi/standard:
                description: Base profile
            features:
              async_client:
                enabled: true
                description: Async runtime
            """
        ).strip()
    )
    (modules_root / "demo" / "module.yaml").write_text("version: 0.1.0\n")

    monkeypatch.setattr(config_loader, "MODULES_PATH", modules_root)
    result = config_loader.load_module_config("demo", profile="fastapi/standard")

    features = result["features"]
    assert features["async_client"]["profiles"] == ["fastapi/standard"]
    assert "demo" in features
    assert features["demo"]["profiles"] == ["fastapi/standard"]
    assert features["demo"]["status"] == "implicit"


def test_load_module_config_uses_profile_hint_when_profiles_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    modules_root = tmp_path / "modules"
    config_dir = modules_root / "demo" / "config"
    config_dir.mkdir(parents=True)

    (config_dir / "base.yaml").write_text(
        textwrap.dedent(
            """
            name: Demo Module
            description: Demo
            features:
              widget:
                enabled: true
            """
        ).strip()
    )
    (modules_root / "demo" / "module.yaml").write_text("version: 0.1.0\n")

    monkeypatch.setattr(config_loader, "MODULES_PATH", modules_root)

    result = config_loader.load_module_config("demo", profile="fastapi/standard")

    assert result["features"]["widget"]["profiles"] == ["fastapi/standard"]
    assert result["features"]["demo"]["profiles"] == ["fastapi/standard"]
