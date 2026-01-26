"""Generator-level guardrails for Inventory."""

from __future__ import annotations

from pathlib import Path


def test_build_base_context(inventory_generator, module_config) -> None:
    context = inventory_generator.build_base_context(module_config)
    assert context["module_name"] == "inventory"
    assert context["module_class_name"] == "InventoryService"
    assert context["inventory_defaults"]["default_currency"] == "usd"
    assert isinstance(context["inventory_snippet_catalog"], list)


def test_generate_vendor_and_variant_outputs(
    inventory_generator,
    module_config,
    tmp_path: Path,
) -> None:
    renderer = inventory_generator.create_renderer()
    base_context = inventory_generator.apply_base_context_overrides(
        inventory_generator.build_base_context(module_config)
    )

    inventory_generator.generate_vendor_files(module_config, tmp_path, renderer, base_context)
    vendor_runtime = (
        tmp_path
        / ".rapidkit"
        / "vendor"
        / base_context["rapidkit_vendor_module"]
        / base_context["rapidkit_vendor_version"]
        / "src"
        / "modules"
        / "free"
        / "billing"
        / "inventory"
        / "inventory.py"
    )
    assert vendor_runtime.exists()

    inventory_generator.generate_variant_files("fastapi", tmp_path, renderer, base_context)
    assert (
        tmp_path / "src" / "modules" / "free" / "billing" / "inventory" / "inventory.py"
    ).exists()
    assert (
        tmp_path / "src" / "modules" / "free" / "billing" / "inventory" / "routers" / "inventory.py"
    ).exists()

    inventory_generator.generate_variant_files("nestjs", tmp_path, renderer, base_context)
    service_file = (
        tmp_path / "src" / "modules" / "free" / "billing" / "inventory" / "inventory.service.ts"
    )
    controller_file = (
        tmp_path / "src" / "modules" / "free" / "billing" / "inventory" / "inventory.controller.ts"
    )
    module_file = (
        tmp_path / "src" / "modules" / "free" / "billing" / "inventory" / "inventory.module.ts"
    )
    configuration_file = tmp_path / "nestjs" / "configuration.js"

    for artefact in (service_file, controller_file, module_file, configuration_file):
        assert artefact.exists(), f"Expected NestJS artefact {artefact} to exist"
        assert artefact.read_text().strip(), f"Generated file {artefact} is empty"

    controller_src = controller_file.read_text()
    assert (
        "@Controller('inventory')" in controller_src or '@Controller("inventory")' in controller_src
    ), "NestJS controller should declare inventory route"
    assert "@Get('health')" in controller_src or '@Get("health")' in controller_src
    assert "@Get('items')" in controller_src or '@Get("items")' in controller_src
    assert "@Post('items/:sku')" in controller_src or '@Post("items/:sku")' in controller_src
    assert (
        "@Post('items/:sku/adjust')" in controller_src
        or '@Post("items/:sku/adjust")' in controller_src
    )


def test_core_files_exist(module_root: Path) -> None:
    expected = [
        "module.yaml",
        "generate.py",
        "overrides.py",
        "config/base.yaml",
        "config/snippets.yaml",
        "module.verify.json",
        ".module_state.json",
    ]
    for rel_path in expected:
        assert (module_root / rel_path).exists(), rel_path


def test_framework_files_exist(module_root: Path) -> None:
    expected = [
        "frameworks/fastapi.py",
        "frameworks/nestjs.py",
    ]
    for rel_path in expected:
        assert (module_root / rel_path).exists(), rel_path


def test_templates_exist(module_root: Path) -> None:
    expected = [
        "templates/base/inventory.py.j2",
        "templates/base/inventory_health.py.j2",
        "templates/base/inventory_types.py.j2",
        "templates/variants/fastapi/inventory.py.j2",
        "templates/variants/fastapi/inventory_routes.py.j2",
        "templates/variants/fastapi/inventory_health.py.j2",
        "templates/variants/nestjs/inventory.service.ts.j2",
        "templates/variants/nestjs/inventory.controller.ts.j2",
        "templates/variants/nestjs/inventory.module.ts.j2",
        "templates/vendor/nestjs/configuration.js.j2",
    ]
    for rel_path in expected:
        assert (module_root / rel_path).exists(), rel_path
