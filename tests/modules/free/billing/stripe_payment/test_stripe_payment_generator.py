"""Generator-level guardrails for Stripe Payment."""

from __future__ import annotations

from pathlib import Path


def test_generate_vendor_and_variant_outputs(
    stripe_payment_generator,
    module_config,
    tmp_path: Path,
) -> None:
    renderer = stripe_payment_generator.create_renderer()
    base_context = stripe_payment_generator.apply_base_context_overrides(
        stripe_payment_generator.build_base_context(module_config)
    )

    stripe_payment_generator.generate_vendor_files(module_config, tmp_path, renderer, base_context)
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
        / "stripe_payment"
        / "stripe_payment.py"
    )
    assert vendor_runtime.exists()

    stripe_payment_generator.generate_variant_files("fastapi", tmp_path, renderer, base_context)
    assert (
        tmp_path / "src" / "modules" / "free" / "billing" / "stripe_payment" / "stripe_payment.py"
    ).exists()
    assert (
        tmp_path
        / "src"
        / "modules"
        / "free"
        / "billing"
        / "stripe_payment"
        / "routers"
        / "stripe_payment.py"
    ).exists()
    assert (
        tmp_path
        / "src"
        / "modules"
        / "free"
        / "billing"
        / "stripe_payment"
        / "types"
        / "stripe_payment.py"
    ).exists()
    assert (tmp_path / "config" / "stripe_payment.yaml").exists()

    stripe_payment_generator.generate_variant_files("nestjs", tmp_path, renderer, base_context)
    base_nest_dir = tmp_path / "src" / "modules" / "free" / "billing" / "stripe_payment"
    service_file = base_nest_dir / "stripe-payment.service.ts"
    controller_file = base_nest_dir / "stripe-payment.controller.ts"
    module_file = base_nest_dir / "stripe-payment.module.ts"
    health_file = tmp_path / "src" / "health" / "stripe-payment.health.ts"
    routes_file = base_nest_dir / "stripe-payment.routes.ts"
    configuration_ts_file = base_nest_dir / "stripe-payment.configuration.ts"
    configuration_file = tmp_path / "nestjs" / "configuration.js"

    for artefact in (
        service_file,
        controller_file,
        module_file,
        health_file,
        routes_file,
        configuration_ts_file,
        configuration_file,
    ):
        assert artefact.exists(), f"Expected NestJS artefact {artefact} to exist"
        assert artefact.read_text().strip(), f"Generated file {artefact} is empty"

    controller_src = controller_file.read_text()
    assert (
        "@Controller('stripe-payment')" in controller_src
        or '@Controller("stripe-payment")' in controller_src
    ), "NestJS controller should declare stripe-payment route"
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
        "templates/base/stripe_payment.py.j2",
        "templates/base/stripe_payment_health.py.j2",
        "templates/base/stripe_payment_types.py.j2",
        "templates/variants/fastapi/stripe_payment.py.j2",
        "templates/variants/fastapi/stripe_payment_routes.py.j2",
        "templates/variants/fastapi/stripe_payment_health.py.j2",
        "templates/variants/fastapi/stripe_payment_types.py.j2",
        "templates/variants/fastapi/stripe_payment_config.yaml.j2",
        "templates/tests/integration/test_stripe_payment_integration.j2",
        "templates/variants/nestjs/stripe_payment.service.ts.j2",
        "templates/variants/nestjs/stripe_payment.controller.ts.j2",
        "templates/variants/nestjs/stripe_payment.module.ts.j2",
        "templates/variants/nestjs/stripe_payment.health.ts.j2",
        "templates/variants/nestjs/stripe_payment.routes.ts.j2",
        "templates/variants/nestjs/stripe_payment.configuration.ts.j2",
        "templates/vendor/nestjs/configuration.js.j2",
    ]
    for rel_path in expected:
        assert (module_root / rel_path).exists(), rel_path
