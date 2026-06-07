from modules.free.tasks.queue_platform.generate import QueuePlatformModuleGenerator


def test_queue_platform_declares_fastapi_and_nestjs_variants() -> None:
    config = QueuePlatformModuleGenerator().load_module_config()
    variants = config["generation"]["variants"]

    assert "fastapi" in variants
    assert "nestjs" in variants
