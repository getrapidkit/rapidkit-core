from modules.free.ai.vector_store.overrides import VectorStoreOverrides


def test_vector_store_overrides_are_configurable() -> None:
    overrides = VectorStoreOverrides()

    assert overrides.get_override_info() == {"method_overrides": [], "setting_overrides": []}
    assert hasattr(overrides, "call_original")
