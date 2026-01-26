from __future__ import annotations

import json
from pathlib import Path

from pytest import MonkeyPatch

from cli.utils.registry import update_registry


def _capture_printers(monkeypatch: MonkeyPatch) -> tuple[list[str], list[str]]:
    success_msgs: list[str] = []
    warning_msgs: list[str] = []
    monkeypatch.setattr("cli.utils.registry.print_success", lambda msg: success_msgs.append(msg))
    monkeypatch.setattr("cli.utils.registry.print_warning", lambda msg: warning_msgs.append(msg))
    return success_msgs, warning_msgs


def test_update_registry_creates_file_and_appends(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    success_msgs, warning_msgs = _capture_printers(monkeypatch)

    update_registry("logging", tmp_path)

    registry_path = tmp_path / "registry.json"
    data = json.loads(registry_path.read_text())
    assert data == {"installed_modules": [{"slug": "logging"}]}
    assert any("logging" in msg for msg in success_msgs)
    assert not warning_msgs

    # Second call should not duplicate entries
    update_registry("logging", tmp_path)
    data = json.loads(registry_path.read_text())
    assert data == {"installed_modules": [{"slug": "logging"}]}


def test_update_registry_handles_corrupt_file(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    success_msgs, warning_msgs = _capture_printers(monkeypatch)

    registry_path = tmp_path / "registry.json"
    registry_path.write_text("not-json", encoding="utf-8")

    update_registry("analytics", tmp_path)

    assert success_msgs == ["✅ Updated registry with module: analytics"]
    assert warning_msgs == []
