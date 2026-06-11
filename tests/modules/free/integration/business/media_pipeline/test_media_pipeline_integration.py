import importlib.util
import sys
from pathlib import Path

from modules.free.business.media_pipeline.generate import MediaPipelineModuleGenerator


def _load_module(name: str, path: Path) -> object:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generated module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_media_pipeline_integration_audit_flow(tmp_path: Path) -> None:
    generator = MediaPipelineModuleGenerator()
    config = generator.load_module_config()
    context = generator.build_base_context(config)
    renderer = generator.create_renderer()
    generator.generate_vendor_files(config, tmp_path, renderer, context)
    vendor = _load_module(
        "integration_media_pipeline_vendor",
        tmp_path
        / ".rapidkit"
        / "vendor"
        / config["name"]
        / config["version"]
        / "src/modules/free/business/media_pipeline"
        / "media_pipeline.py",
    )
    pipeline = vendor.MediaPipeline()

    pipeline.ingest_and_process(vendor.MediaSource("clip.mp4", b"video", "video/mp4"))

    assert [entry["event"] for entry in pipeline.audit_log()] == [
        "media.ingested",
        "media.processed",
    ]
