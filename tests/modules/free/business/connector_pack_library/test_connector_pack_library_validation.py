import pytest


def test_connector_pack_library_validates_required_input(rendered_connector_pack_library) -> None:
    vendor = rendered_connector_pack_library["vendor"]
    with pytest.raises(vendor.ConnectorPackLibraryError, match="required"):
        vendor.ConnectorPackLibrary().register_pack(
            key="", provider="", display_name="Bad", scopes=("read",)
        )
