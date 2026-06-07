from modules.free.business.connector_hub.overrides import ConnectorHubOverrides


def test_connector_hub_overrides_are_configurable() -> None:
    overrides = ConnectorHubOverrides()

    assert overrides.get_override_info() == {"method_overrides": [], "setting_overrides": []}
    assert hasattr(overrides, "call_original")
