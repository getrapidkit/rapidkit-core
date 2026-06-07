from modules.free.tasks.queue_platform.generate import QueuePlatformModuleGenerator


def test_queue_platform_module_metadata_is_stable_enterprise_ready() -> None:
    config = QueuePlatformModuleGenerator().load_module_config()

    assert config["status"] == "stable"
    assert config["testing"]["coverage_min"] >= 85
    assert config["metadata"]["enterprise_ready"] is True
