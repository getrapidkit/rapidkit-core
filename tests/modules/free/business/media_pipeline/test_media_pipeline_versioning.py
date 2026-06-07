from modules.free.business.media_pipeline.generate import MediaPipelineModuleGenerator


def test_media_pipeline_declares_semver_version() -> None:
    config = MediaPipelineModuleGenerator().load_module_config()
    parts = str(config["version"]).split(".")

    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)
