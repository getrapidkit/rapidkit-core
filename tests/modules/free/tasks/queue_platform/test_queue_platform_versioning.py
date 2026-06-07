from modules.free.tasks.queue_platform.generate import QueuePlatformModuleGenerator


def test_queue_platform_declares_semver_version() -> None:
    config = QueuePlatformModuleGenerator().load_module_config()
    parts = str(config["version"]).split(".")

    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)
