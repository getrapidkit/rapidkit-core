import pytest


def test_connector_pack_library_raises_domain_error_for_missing_resource(
    rendered_connector_pack_library,
) -> None:
    vendor = rendered_connector_pack_library["vendor"]
    library = vendor.ConnectorPackLibrary()

    with pytest.raises(vendor.ConnectorPackLibraryError, match="not found"):
        library.install_pack("missing", actor_id="admin")
