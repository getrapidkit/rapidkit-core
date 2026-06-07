from modules.free.business.document_pipeline.generate import DocumentPipelineModuleGenerator


def test_document_pipeline_manifest_is_stable() -> None:
    config = DocumentPipelineModuleGenerator().load_module_config()
    assert config["status"] == "stable"
    assert config["version"].count(".") == 2
