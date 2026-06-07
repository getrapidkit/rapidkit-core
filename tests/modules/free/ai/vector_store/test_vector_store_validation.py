import pytest


def test_vector_store_rejects_disabled_runtime(rendered_vector_store) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_vector_store["vendor"]
    store = vendor.VectorStore(vendor.VectorStoreConfig(enabled=False))

    with pytest.raises(vendor.VectorStoreError, match="disabled"):
        store.upsert(id="disabled", vector=[1, 0])


def test_vector_store_requires_non_empty_vectors(rendered_vector_store) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_vector_store["vendor"]
    store = vendor.VectorStore()

    with pytest.raises(vendor.VectorStoreError, match="at least one"):
        store.upsert(id="empty", vector=[])
