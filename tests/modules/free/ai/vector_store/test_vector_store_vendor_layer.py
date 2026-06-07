def test_vector_store_vendor_exports_runtime_contract(rendered_vector_store) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_vector_store["vendor"]

    for name in (
        "VectorStore",
        "InMemoryVectorStore",
        "VectorStoreConfig",
        "VectorStoreError",
        "VectorDocument",
        "VectorSearchResult",
        "cosine_similarity",
    ):
        assert hasattr(vendor, name)

    assert vendor.cosine_similarity([1, 0], [1, 0]) == 1.0
