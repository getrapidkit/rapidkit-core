import importlib.util
import sys
from pathlib import Path

from modules.free.tasks.queue_platform.generate import QueuePlatformModuleGenerator


def _load_module(name: str, path: Path) -> object:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generated module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_queue_platform_integration_worker_flow(tmp_path: Path) -> None:
    generator = QueuePlatformModuleGenerator()
    config = generator.load_module_config()
    context = generator.build_base_context(config)
    renderer = generator.create_renderer()
    generator.generate_vendor_files(config, tmp_path, renderer, context)
    vendor = _load_module(
        "integration_queue_platform_vendor",
        tmp_path
        / ".rapidkit"
        / "vendor"
        / config["name"]
        / config["version"]
        / "src/modules/free/tasks/queue_platform"
        / "queue_platform.py",
    )
    queue = vendor.QueuePlatform()

    queue.enqueue("exports", {"format": "csv"}, tenant_id="tenant-a")
    queue.process_once(
        "exports", lambda message: message.metadata.update({"worker": "ok"}), tenant_id="tenant-a"
    )

    assert queue.list_messages(status=vendor.QueueMessageStatus.ACKED)[0].metadata["worker"] == "ok"
