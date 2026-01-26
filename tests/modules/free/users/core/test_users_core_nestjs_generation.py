from importlib import import_module
from pathlib import Path


def test_nestjs_generator_creates_metadata_controller(tmp_path: Path) -> None:
    module = import_module("modules.free.users.users_core.generate")

    renderer = module.TemplateRenderer(module.MODULE_ROOT / "templates")
    config = module.load_module_config()
    base_context = module.build_base_context(config)

    # First write vendor + runtime outputs then materialise nestjs variant
    module.generate_vendor_files(config, tmp_path, renderer, base_context)
    module.generate_variant_files("nestjs", tmp_path, renderer, base_context)

    metadata_path = (
        tmp_path
        / "src"
        / "modules"
        / "free"
        / "users"
        / "users_core"
        / "core"
        / "users"
        / "metadata.controller.ts"
    )
    assert metadata_path.exists(), "NestJS metadata controller should be generated"
