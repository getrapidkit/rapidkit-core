def test_connector_hub_executes_registered_operation(rendered_connector_hub) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_connector_hub["vendor"]
    hub = vendor.ConnectorHub()
    hub.register_connector(
        vendor.ConnectorDefinition(
            key="stripe",
            display_name="Stripe",
            operations=("sync_customer",),
            required_secrets=("api_key",),
        ),
        handlers={"sync_customer": lambda payload, _context: {"synced": payload["id"]}},
    )
    connection = hub.connect(
        connector="stripe",
        tenant_id="tenant-a",
        secrets={"api_key": "sk_test"},
    )

    run = hub.execute(
        connection_id=connection.id,
        operation="sync_customer",
        payload={"id": "cus_1"},
    )

    assert run.status == "succeeded"
    assert run.output == {"synced": "cus_1"}
    assert hub.list_connections(tenant_id="tenant-a")[0]["secrets"] == {"api_key": "***"}


def test_connector_hub_execute_is_idempotent_per_connection(rendered_connector_hub) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_connector_hub["vendor"]
    hub = vendor.ConnectorHub()
    hub.register_connector(
        vendor.ConnectorDefinition(
            key="stripe",
            display_name="Stripe",
            operations=("sync_customer",),
            required_secrets=("api_key",),
        ),
        handlers={"sync_customer": lambda payload, _context: {"synced": payload["id"]}},
    )
    connection = hub.connect(
        connector="stripe", tenant_id="tenant-a", secrets={"api_key": "sk_test"}
    )

    first = hub.execute(
        connection_id=connection.id,
        operation="sync_customer",
        payload={"id": "cus_1"},
        idempotency_key="run-1",
    )
    second = hub.execute(
        connection_id=connection.id,
        operation="sync_customer",
        payload={"id": "cus_1"},
        idempotency_key="run-1",
    )

    assert second.id == first.id
