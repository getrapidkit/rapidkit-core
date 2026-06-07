def test_connector_hub_health_reports_registry_stats(rendered_connector_hub) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_connector_hub["vendor"]
    hub = vendor.ConnectorHub()
    hub.register_connector(vendor.ConnectorDefinition("x", "X", ("sync",)))

    health = hub.health()

    assert health["module"] == "connector_hub"
    assert health["status"] == "ok"
    assert health["stats"]["connectors"] == 1
    assert health["stats"]["audit_events"] >= 1
