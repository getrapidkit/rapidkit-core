from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from modules.free.ai.rag_pipeline.generate import RagPipelineModuleGenerator


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generated module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_free_ai_rag_pipeline_generates_retrieves_and_answers(tmp_path: Path) -> None:
    generator = RagPipelineModuleGenerator()
    config = generator.load_module_config()
    context = generator.build_base_context(config)
    renderer = generator.create_renderer()

    generator.generate_vendor_files(config, tmp_path, renderer, context)
    vendor_path = (
        tmp_path
        / ".rapidkit/vendor"
        / config["name"]
        / config["version"]
        / "src/modules/free/ai/rag_pipeline/rag_pipeline.py"
    )
    vendor = _load_module("integration_rag_pipeline_vendor", vendor_path)

    pipeline = vendor.RagPipeline()
    first = pipeline.ingest(
        id="release",
        text="RapidKit marketplace products need manifests, checksums, docs, and support gates.",
        metadata={"kind": "release", "tenant_id": "tenant-a"},
        namespace="tenant-a",
        idempotency_key="release-doc-v1",
    )
    second = pipeline.ingest(
        id="ignored",
        text="ignored",
        metadata={"kind": "release", "tenant_id": "tenant-a"},
        namespace="tenant-a",
        idempotency_key="release-doc-v1",
    )

    answer = pipeline.answer(
        "What do marketplace products need?", namespace="tenant-a", tenant_id="tenant-a"
    )

    assert answer.citations[0].document_id == "release"
    assert "RapidKit marketplace products" in answer.answer
    assert answer.metadata["citation_count"] == 1
    assert second.id == first.id
    assert pipeline.audit_events(event_type="answer.generated")
