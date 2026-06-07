def test_vector_store_upserts_and_queries_by_similarity(rendered_vector_store) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_vector_store["vendor"]
    store = vendor.VectorStore(vendor.VectorStoreConfig(dimensions=3))

    store.upsert(id="alpha", vector=[1, 0, 0], text="alpha", metadata={"tenant_id": "acme"})
    store.upsert(id="beta", vector=[0, 1, 0], text="beta", metadata={"tenant_id": "acme"})

    results = store.query(vector=[0.95, 0.05, 0], top_k=1)

    assert results[0].document.id == "alpha"
    assert results[0].score > 0.99


def test_vector_store_filters_by_namespace_and_metadata(rendered_vector_store) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_vector_store["vendor"]
    store = vendor.VectorStore()

    store.upsert(id="public", vector=[1, 0], namespace="default", metadata={"tier": "free"})
    store.upsert(id="private", vector=[1, 0], namespace="tenant-a", metadata={"tier": "pro"})

    results = store.query(
        vector=[1, 0],
        namespace="tenant-a",
        metadata_filter={"tier": "pro"},
    )

    assert [result.document.id for result in results] == ["private"]
    assert store.query(vector=[1, 0], metadata_filter={"tier": "pro"}) == []


def test_vector_store_upsert_is_idempotent_per_namespace(rendered_vector_store) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_vector_store["vendor"]
    store = vendor.VectorStore()

    first = store.upsert(vector=[1, 0], namespace="tenant-a", idempotency_key="doc-1")
    second = store.upsert(vector=[0, 1], namespace="tenant-a", idempotency_key="doc-1")

    assert second.id == first.id
    assert store.stats()["documents"] == 1


def test_vector_store_delete_and_clear_update_stats(rendered_vector_store) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_vector_store["vendor"]
    store = vendor.VectorStore()

    store.upsert(id="one", vector=[1, 0])
    store.upsert(id="two", vector=[0, 1], namespace="archive")

    assert store.delete("one") is True
    assert store.delete("missing") is False
    assert store.clear(namespace="archive") == 1
    assert store.stats()["documents"] == 0
    assert store.stats()["audit_events"] >= 3
