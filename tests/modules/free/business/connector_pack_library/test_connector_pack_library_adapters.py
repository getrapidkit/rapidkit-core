def test_connector_pack_library_exposes_runtime_contract(rendered_connector_pack_library) -> None:
    vendor = rendered_connector_pack_library["vendor"]

    assert hasattr(vendor, "ConnectorPackLibrary")
    assert hasattr(vendor, "ConnectorPack")
    assert hasattr(vendor, "ConnectorStatus")
