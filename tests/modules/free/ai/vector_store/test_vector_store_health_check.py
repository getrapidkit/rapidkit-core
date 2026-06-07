def test_vector_store_health_reports_index_stats(rendered_vector_store) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_vector_store["vendor"]
    store = vendor.VectorStore()
    store.upsert(id="doc", vector=[1, 0], namespace="tenant-a")

    health = store.health()

    assert health["module"] == "vector_store"
    assert health["status"] == "ok"
    assert health["stats"]["documents"] == 1
    assert health["stats"]["namespaces"] == {"tenant-a": 1}
    assert health["stats"]["audit_events"] >= 1
