import pytest


def test_connector_hub_requires_declared_secrets(rendered_connector_hub) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_connector_hub["vendor"]
    hub = vendor.ConnectorHub()
    hub.register_connector(vendor.ConnectorDefinition("github", "GitHub", ("sync",), ("token",)))

    with pytest.raises(vendor.ConnectorHubError, match="missing"):
        hub.connect(connector="github", tenant_id="tenant", secrets={})


def test_connector_hub_rejects_unsupported_operation(rendered_connector_hub) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_connector_hub["vendor"]
    hub = vendor.ConnectorHub()
    hub.register_connector(vendor.ConnectorDefinition("x", "X", ("sync",)))
    connection = hub.connect(connector="x", tenant_id="tenant", secrets={})

    with pytest.raises(vendor.ConnectorHubError, match="operation"):
        hub.execute(connection_id=connection.id, operation="delete")


def test_connector_hub_rejects_cross_tenant_execution(rendered_connector_hub) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_connector_hub["vendor"]
    hub = vendor.ConnectorHub()
    hub.register_connector(vendor.ConnectorDefinition("x", "X", ("sync",)))
    connection = hub.connect(connector="x", tenant_id="tenant-a", secrets={})

    with pytest.raises(vendor.ConnectorHubError, match="tenant"):
        hub.execute(connection_id=connection.id, operation="sync", tenant_id="tenant-b")


def test_connector_hub_rejects_inactive_connection(rendered_connector_hub) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_connector_hub["vendor"]
    hub = vendor.ConnectorHub()
    hub.register_connector(vendor.ConnectorDefinition("x", "X", ("sync",)))
    connection = hub.connect(connector="x", tenant_id="tenant-a", secrets={})
    hub.deactivate_connection(connection.id)

    with pytest.raises(vendor.ConnectorHubError, match="inactive"):
        hub.execute(connection_id=connection.id, operation="sync")
