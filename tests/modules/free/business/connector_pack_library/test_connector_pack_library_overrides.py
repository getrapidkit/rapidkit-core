from modules.free.business.connector_pack_library import overrides


def test_connector_pack_library_overrides_contract_loads() -> None:
    assert hasattr(overrides, "ConnectorPackLibraryOverrides")
