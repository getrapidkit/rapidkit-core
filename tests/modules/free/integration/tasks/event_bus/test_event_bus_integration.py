from pathlib import Path

from modules.free.tasks.event_bus.generate import EventBusModuleGenerator


def test_free_tasks_event_bus_generated_vendor_smoke(tmp_path: Path) -> None:
    generator = EventBusModuleGenerator()
    config = generator.load_module_config()
    context = generator.build_base_context(config)
    renderer = generator.create_renderer()
    generator.generate_vendor_files(config, tmp_path, renderer, context)

    assert (tmp_path / ".rapidkit" / "vendor" / config["name"] / config["version"]).exists()
