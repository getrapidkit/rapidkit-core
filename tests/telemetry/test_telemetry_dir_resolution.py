"""Tests for safe telemetry directory resolution.

These tests ensure we don't accidentally create directories like
core/MagicMock/mock.telemetry_dir due to MagicMock-derived inputs.
"""

import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from core.telemetry.collector import TelemetryCollector


def _resolved_dir(cfg: object) -> Path:
    # Disable telemetry to avoid background threads and fs writes
    os.environ["RAPIDKIT_TELEMETRY"] = "0"
    tc = TelemetryCollector(config=cfg)
    return Path(tc.get_telemetry_status()["telemetry_dir"])


def test_magicmock_candidate_is_ignored() -> None:
    default_dir = Path.home() / ".rapidkit" / "telemetry"
    cfg = SimpleNamespace(telemetry_dir=MagicMock())
    assert _resolved_dir(cfg) == default_dir


def test_magicmock_like_string_is_ignored() -> None:
    default_dir = Path.home() / ".rapidkit" / "telemetry"
    cfg = SimpleNamespace(telemetry_dir='<MagicMock name="telemetry_dir">')
    assert _resolved_dir(cfg) == default_dir


def test_suspicious_components_are_ignored() -> None:
    default_dir = Path.home() / ".rapidkit" / "telemetry"
    suspicious = Path.cwd() / "MagicMock" / "mock.telemetry_dir" / "123"
    cfg = SimpleNamespace(telemetry_dir=str(suspicious))
    assert _resolved_dir(cfg) == default_dir


def test_relative_path_is_nested_under_default() -> None:
    default_dir = Path.home() / ".rapidkit" / "telemetry"
    rel = "relative/path"
    cfg = SimpleNamespace(telemetry_dir=rel)
    resolved = _resolved_dir(cfg)
    assert str(resolved).startswith(str(default_dir))
    assert resolved == default_dir / rel


def test_absolute_safe_path_is_accepted(tmp_path: Path) -> None:
    abs_p = tmp_path / "telemetry_here"
    cfg = SimpleNamespace(telemetry_dir=str(abs_p))
    assert _resolved_dir(cfg) == abs_p
