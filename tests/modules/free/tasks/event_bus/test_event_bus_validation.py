from modules.free.tasks.event_bus.generate import EventBusModuleGenerator


def test_event_bus_manifest_has_capabilities() -> None:
    config = EventBusModuleGenerator().load_module_config()
    assert config.get("capabilities")
