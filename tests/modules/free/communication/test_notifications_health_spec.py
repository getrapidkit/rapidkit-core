from __future__ import annotations

from pathlib import Path

from modules.shared.utils.health_specs import build_standard_health_spec


def test_notifications_builds_standard_health_spec() -> None:
    module_root = (
        Path(__file__).resolve().parents[4] / "src/modules/free/communication/notifications"
    )
    spec = build_standard_health_spec(module_root)

    # vendor template exists and infers a health runtime
    assert spec.vendor_relative_path
    # vendor placement updated to use canonical public path; accept either
    assert "notifications" in spec.vendor_relative_path

    # target paths follow the standard health shim conventions (public canonical src/health)
    assert spec.target_relative_path.endswith("src/health/notifications.py")
