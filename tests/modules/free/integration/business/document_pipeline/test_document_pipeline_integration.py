from pathlib import Path

from modules.free.business.document_pipeline.generate import DocumentPipelineModuleGenerator


def test_free_business_document_pipeline_generated_vendor_smoke(tmp_path: Path) -> None:
    generator = DocumentPipelineModuleGenerator()
    config = generator.load_module_config()
    context = generator.build_base_context(config)
    renderer = generator.create_renderer()
    generator.generate_vendor_files(config, tmp_path, renderer, context)

    assert (tmp_path / ".rapidkit" / "vendor" / config["name"] / config["version"]).exists()
