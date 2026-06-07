from modules.free.business.document_pipeline.generate import DocumentPipelineModuleGenerator


def test_document_pipeline_declares_fastapi_and_nestjs_variants() -> None:
    config = DocumentPipelineModuleGenerator().load_module_config()
    variants = config["generation"]["variants"]
    assert "fastapi" in variants
    assert "nestjs" in variants
