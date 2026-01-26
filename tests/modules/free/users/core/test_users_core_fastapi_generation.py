from importlib import import_module
from pathlib import Path


def test_fastapi_generator_creates_metadata_and_health(tmp_path: Path) -> None:
    module = import_module("modules.free.users.users_core.generate")

    renderer = module.TemplateRenderer(module.MODULE_ROOT / "templates")
    config = module.load_module_config()
    base_context = module.build_base_context(config)

    # Generate vendor + fastapi variant into tmp
    module.generate_vendor_files(config, tmp_path, renderer, base_context)
    module.generate_variant_files("fastapi", tmp_path, renderer, base_context)

    metadata_path = (
        tmp_path
        / "src"
        / "modules"
        / "free"
        / "users"
        / "users_core"
        / "core"
        / "users"
        / "metadata_routes.py"
    )
    health_path = (
        tmp_path / "src" / "modules" / "free" / "users" / "users_core" / "health" / "users_core.py"
    )

    legacy_public_health = tmp_path / "src" / "health" / "users_core.py"
    legacy_private_health_init = tmp_path / "src" / "core" / "health" / "__init__.py"

    assert metadata_path.exists(), "FastAPI metadata routes should be generated"
    assert not health_path.exists(), "Module-local health snapshot should not be generated"
    assert legacy_public_health.exists(), "Public health wrapper should be created under src/health"
    assert (
        not legacy_private_health_init.exists()
    ), "Legacy src/core/health compatibility shims should not be generated"
