from modules.free.business.media_pipeline.generate import MediaPipelineModuleGenerator


def test_media_pipeline_module_metadata_is_stable_enterprise_ready() -> None:
    config = MediaPipelineModuleGenerator().load_module_config()

    assert config["status"] == "stable"
    assert config["testing"]["coverage_min"] >= 85
    assert config["metadata"]["enterprise_ready"] is True
