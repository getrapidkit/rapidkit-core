def test_connector_hub_vendor_exports_runtime_contract(rendered_connector_hub) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_connector_hub["vendor"]

    for name in (
        "ConnectorHub",
        "ConnectorHubConfig",
        "ConnectorHubError",
        "ConnectorDefinition",
        "ConnectorConnection",
        "ConnectorRun",
        "redact_secrets",
    ):
        assert hasattr(vendor, name)
