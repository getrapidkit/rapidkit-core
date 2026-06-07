import pytest


def test_vector_store_rejects_dimension_mismatch(rendered_vector_store) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_vector_store["vendor"]
    store = vendor.VectorStore(vendor.VectorStoreConfig(dimensions=3))

    with pytest.raises(vendor.VectorStoreError, match="dimensions"):
        store.upsert(id="bad", vector=[1, 2])


def test_vector_store_rejects_invalid_query_limits(rendered_vector_store) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_vector_store["vendor"]
    store = vendor.VectorStore(vendor.VectorStoreConfig(max_top_k=2))

    with pytest.raises(vendor.VectorStoreError, match="top_k"):
        store.query(vector=[1, 0], top_k=3)


def test_vector_store_rejects_nan_values(rendered_vector_store) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_vector_store["vendor"]
    store = vendor.VectorStore()

    with pytest.raises(vendor.VectorStoreError, match="NaN"):
        store.upsert(id="nan", vector=[float("nan")])
