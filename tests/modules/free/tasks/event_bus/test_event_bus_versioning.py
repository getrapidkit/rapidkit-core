from modules.free.tasks.event_bus.generate import EventBusModuleGenerator


def test_event_bus_manifest_is_stable() -> None:
    config = EventBusModuleGenerator().load_module_config()
    assert config["status"] == "stable"
    assert config["version"].count(".") == 2
