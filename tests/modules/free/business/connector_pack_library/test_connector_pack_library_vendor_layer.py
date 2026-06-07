def test_connector_pack_library_vendor_runtime_is_generated(
    rendered_connector_pack_library,
) -> None:
    root = rendered_connector_pack_library["root"]

    assert (
        root
        / ".rapidkit/vendor/connector_pack_library/0.1.3/src/business/connector_pack_library.py"
    ).exists()
