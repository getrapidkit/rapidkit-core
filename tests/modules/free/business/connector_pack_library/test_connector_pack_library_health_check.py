def test_connector_pack_library_health_reports_runtime_state(
    rendered_connector_pack_library,
) -> None:
    vendor = rendered_connector_pack_library["vendor"]
    library = vendor.ConnectorPackLibrary()
    library.register_pack(
        key="stripe", provider="stripe", display_name="Stripe", scopes=("payments:read",)
    )
    library.install_pack("stripe", actor_id="admin")

    health = library.health()
    assert health["packs"] == 1
    assert health["installed"] == 1
