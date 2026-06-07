import pytest


def test_connector_hub_rejects_disabled_runtime(rendered_connector_hub) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_connector_hub["vendor"]
    hub = vendor.ConnectorHub(vendor.ConnectorHubConfig(enabled=False))

    with pytest.raises(vendor.ConnectorHubError, match="disabled"):
        hub.register_connector(vendor.ConnectorDefinition("x", "X", ("sync",)))


def test_connector_hub_requires_operations(rendered_connector_hub) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_connector_hub["vendor"]
    hub = vendor.ConnectorHub()

    with pytest.raises(vendor.ConnectorHubError, match="operation"):
        hub.register_connector(vendor.ConnectorDefinition("x", "X", ()))
