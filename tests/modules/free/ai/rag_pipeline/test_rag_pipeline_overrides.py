from modules.free.ai.rag_pipeline.overrides import RagPipelineOverrides


def test_rag_pipeline_overrides_are_configurable() -> None:
    overrides = RagPipelineOverrides()

    assert overrides.get_override_info() == {"method_overrides": [], "setting_overrides": []}
    assert hasattr(overrides, "call_original")
