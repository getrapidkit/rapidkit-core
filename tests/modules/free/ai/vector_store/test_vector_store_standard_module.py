def test_vector_store_generated_runtime_is_usable(rendered_vector_store) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_vector_store["vendor"]

    store = vendor.VectorStore()
    document = store.upsert(id="doc", vector=[1, 0], text="hello")

    assert document.id == "doc"
    assert store.get("doc").text == "hello"
