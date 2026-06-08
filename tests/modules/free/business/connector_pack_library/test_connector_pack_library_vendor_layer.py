def test_connector_pack_library_vendor_runtime_is_generated(
    rendered_connector_pack_library,
) -> None:
    root = rendered_connector_pack_library["root"]
    config = rendered_connector_pack_library["config"]

    assert (
        root
        / ".rapidkit"
        / "vendor"
        / config["name"]
        / config["version"]
        / "src/modules/free/business/connector_pack_library/connector_pack_library.py"
    ).exists()
