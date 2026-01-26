from __future__ import annotations

from pathlib import Path

from modules.shared.utils.health_specs import build_standard_health_spec


def test_standard_health_spec_targets_public_src(tmp_path: Path) -> None:
    """Ensure build_standard_health_spec chooses the canonical public src/health path."""

    # sample module roots to exercise the health spec inference
    candidates = (
        Path(__file__).resolve().parents[4] / "src/modules/free/essentials/settings",
        Path(__file__).resolve().parents[4] / "src/modules/free/essentials/middleware",
        Path(__file__).resolve().parents[4] / "src/modules/free/essentials/logging",
        Path(__file__).resolve().parents[4] / "src/modules/free/database/db_postgres",
    )

    for module_root in candidates:
        spec = build_standard_health_spec(module_root)
        assert spec.target_relative_path.startswith(
            "src/health/"
        ), f"Expected spec for {module_root.name} to target src/health/ but got {spec.target_relative_path}"
