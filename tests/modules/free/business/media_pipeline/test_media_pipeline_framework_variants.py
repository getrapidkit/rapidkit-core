from modules.free.business.media_pipeline.generate import MediaPipelineModuleGenerator


def test_media_pipeline_declares_fastapi_and_nestjs_variants() -> None:
    config = MediaPipelineModuleGenerator().load_module_config()
    variants = config["generation"]["variants"]

    assert "fastapi" in variants
    assert "nestjs" in variants
