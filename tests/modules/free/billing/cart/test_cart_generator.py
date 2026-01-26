"""Generator-level guardrails for Cart."""

from __future__ import annotations

from pathlib import Path


def test_build_base_context(cart_module_generator, module_config) -> None:
    context = cart_module_generator.build_base_context(module_config)
    assert context["module_name"] == "cart"
    assert "cart_defaults" in context
    assert context["python_runtime_relative"].endswith("src/modules/free/billing/cart/cart.py")


def test_generate_vendor_and_variant_outputs(
    cart_module_generator, module_config, tmp_path: Path
) -> None:
    renderer = cart_module_generator.create_renderer()
    base_context = cart_module_generator.apply_base_context_overrides(
        cart_module_generator.build_base_context(module_config)
    )

    cart_module_generator.generate_vendor_files(module_config, tmp_path, renderer, base_context)
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
        / "cart"
        / "cart.py"
    )
    assert vendor_runtime.exists()

    cart_module_generator.generate_variant_files("fastapi", tmp_path, renderer, base_context)
    assert (tmp_path / "src" / "modules" / "free" / "billing" / "cart" / "cart.py").exists()
    assert (
        tmp_path / "src" / "modules" / "free" / "billing" / "cart" / "routers" / "cart.py"
    ).exists()

    cart_module_generator.generate_variant_files("nestjs", tmp_path, renderer, base_context)
    service_file = tmp_path / "src" / "modules" / "free" / "billing" / "cart" / "cart.service.ts"
    controller_file = (
        tmp_path / "src" / "modules" / "free" / "billing" / "cart" / "cart.controller.ts"
    )
    module_file = tmp_path / "src" / "modules" / "free" / "billing" / "cart" / "cart.module.ts"
    configuration_file = tmp_path / "nestjs" / "configuration.js"

    for artefact in (service_file, controller_file, module_file, configuration_file):
        assert artefact.exists(), f"Expected NestJS artefact {artefact} to exist"
        assert artefact.read_text().strip(), f"Generated file {artefact} is empty"

    controller_src = controller_file.read_text()
    assert (
        "@Controller('cart')" in controller_src or '@Controller("cart")' in controller_src
    ), "NestJS controller should declare cart route"
    assert "@Get('health')" in controller_src or '@Get("health")' in controller_src


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
        "templates/base/cart.py.j2",
        "templates/base/cart_health.py.j2",
        "templates/base/cart_types.py.j2",
        "templates/variants/fastapi/cart.py.j2",
        "templates/variants/fastapi/cart_routes.py.j2",
        "templates/variants/fastapi/cart_health.py.j2",
        "templates/variants/nestjs/cart.service.ts.j2",
        "templates/variants/nestjs/cart.controller.ts.j2",
        "templates/variants/nestjs/cart.module.ts.j2",
        "templates/vendor/nestjs/configuration.js.j2",
    ]
    for rel_path in expected:
        assert (module_root / rel_path).exists(), rel_path
