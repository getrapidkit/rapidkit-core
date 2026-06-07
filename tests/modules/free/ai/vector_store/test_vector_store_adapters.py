def test_vector_store_bulk_upsert_accepts_portable_payloads(rendered_vector_store) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_vector_store["vendor"]
    store = vendor.VectorStore()

    documents = store.bulk_upsert(
        [
            {"id": "one", "vector": [1, 0], "metadata": {"source": "docs"}},
            {"id": "two", "vector": [0, 1], "metadata": {"source": "tickets"}},
        ]
    )

    assert [document.id for document in documents] == ["one", "two"]
    assert store.stats()["documents"] == 2
