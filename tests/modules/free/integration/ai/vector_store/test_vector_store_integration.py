from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from modules.free.ai.vector_store.generate import VectorStoreModuleGenerator


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generated module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_free_ai_vector_store_generates_and_filters_documents(tmp_path: Path) -> None:
    generator = VectorStoreModuleGenerator()
    config = generator.load_module_config()
    context = generator.build_base_context(config)
    renderer = generator.create_renderer()

    generator.generate_vendor_files(config, tmp_path, renderer, context)
    vendor_path = (
        tmp_path
        / ".rapidkit/vendor"
        / config["name"]
        / config["version"]
        / "src/modules/free/ai/vector_store/vector_store.py"
    )
    vendor = _load_module("integration_vector_store_vendor", vendor_path)

    store = vendor.VectorStore(vendor.VectorStoreConfig(dimensions=2))
    first = store.upsert(
        id="free",
        vector=[1, 0],
        text="free product",
        metadata={"tier": "free"},
        idempotency_key="free-doc-v1",
    )
    second = store.upsert(
        id="ignored",
        vector=[0, 1],
        text="ignored",
        metadata={"tier": "free"},
        idempotency_key="free-doc-v1",
    )
    store.upsert(
        id="private",
        vector=[1, 0],
        text="private launch",
        namespace="tenant-a",
        metadata={"tier": "pro"},
    )

    results = store.query(vector=[1, 0], namespace="tenant-a", metadata_filter={"tier": "pro"})

    assert [item.document.id for item in results] == ["private"]
    assert second.id == first.id
    assert store.stats()["documents"] == 2
    assert store.stats()["audit_events"] >= 3
