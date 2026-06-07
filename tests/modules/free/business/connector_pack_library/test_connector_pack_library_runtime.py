from __future__ import annotations

import pytest


def test_connector_pack_library_tracks_install_health_and_rotation(
    rendered_connector_pack_library,
) -> None:
    vendor = rendered_connector_pack_library["vendor"]
    library = vendor.ConnectorPackLibrary()
    pack = library.register_pack(
        key="stripe",
        provider="stripe",
        display_name="Stripe",
        scopes=("payments:read", "webhooks:write"),
    )
    installed = library.install_pack(pack.key, actor_id="admin-1", tenant_id="tenant-1")
    degraded = library.mark_health(pack.key, healthy=False, reason="webhook failures")
    rotated = library.rotate_credentials(pack.key, actor_id="admin-1", reason="scheduled rotation")

    assert installed.status == vendor.ConnectorStatus.INSTALLED
    assert degraded.status == vendor.ConnectorStatus.DEGRADED
    assert rotated.rotated_at is not None
    assert library.health()["packs"] == 1
    assert [event["type"] for event in library.audit_events(key=pack.key)] == [
        "connector.registered",
        "connector.installed",
        "connector.health_updated",
        "connector.credentials_rotated",
    ]


def test_connector_pack_library_validates_scopes_and_rotation_reason(
    rendered_connector_pack_library,
) -> None:
    vendor = rendered_connector_pack_library["vendor"]
    library = vendor.ConnectorPackLibrary()

    with pytest.raises(vendor.ConnectorPackLibraryError, match="scopes"):
        library.register_pack(key="github", provider="github", display_name="GitHub", scopes=())
    library.register_pack(
        key="slack", provider="slack", display_name="Slack", scopes=("chat:write",)
    )
    with pytest.raises(vendor.ConnectorPackLibraryError, match="reason"):
        library.rotate_credentials("slack", actor_id="admin-1", reason="")
