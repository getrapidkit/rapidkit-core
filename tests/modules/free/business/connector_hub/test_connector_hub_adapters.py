def test_connector_hub_default_handler_echoes_payload(rendered_connector_hub) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_connector_hub["vendor"]
    hub = vendor.ConnectorHub()
    hub.register_connector(vendor.ConnectorDefinition("x", "X", ("echo",)))
    connection = hub.connect(connector="x", tenant_id="tenant", secrets={})

    run = hub.execute(connection_id=connection.id, operation="echo", payload={"ok": True})

    assert run.output == {"echo": {"ok": True}}
