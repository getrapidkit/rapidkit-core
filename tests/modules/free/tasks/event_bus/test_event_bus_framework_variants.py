from modules.free.tasks.event_bus.generate import EventBusModuleGenerator


def test_event_bus_declares_fastapi_and_nestjs_variants() -> None:
    config = EventBusModuleGenerator().load_module_config()
    variants = config["generation"]["variants"]
    assert "fastapi" in variants
    assert "nestjs" in variants
