from modules.free.business.document_pipeline.generate import DocumentPipelineModuleGenerator


def test_document_pipeline_manifest_has_capabilities() -> None:
    config = DocumentPipelineModuleGenerator().load_module_config()
    assert config.get("capabilities")
