"""Generator-level guardrails for Observability Core."""

from __future__ import annotations

from pathlib import Path


def test_generate_vendor_and_variant_outputs(
    module_generate,
    module_config,
    tmp_path: Path,
) -> None:
    generator = module_generate.ObservabilityModuleGenerator()
    renderer = generator.create_renderer()
    base_context = generator.apply_base_context_overrides(
        generator.build_base_context(module_config)
    )

    generator.generate_vendor_files(module_config, tmp_path, renderer, base_context)
    vendor_root = (
        tmp_path
        / ".rapidkit"
        / "vendor"
        / str(base_context["rapidkit_vendor_module"])
        / str(base_context["rapidkit_vendor_version"])
        / "src"
    )
    vendor_expected = {
        vendor_root / "modules" / "free" / "observability" / "core" / "observability_core.py",
        vendor_root / "health" / "observability_core.py",
        vendor_root / "modules" / "free" / "observability" / "core" / "observability_core_types.py",
        vendor_root.parent / "nestjs" / "configuration.js",
    }
    for artefact in vendor_expected:
        assert artefact.exists(), f"Expected vendor artefact {artefact}"
        contents = artefact.read_text().strip()
        assert contents, f"Generated vendor file {artefact} is empty"

        relative_path = artefact.relative_to(vendor_root.parent)
        if relative_path == Path("src/modules/free/observability/core/observability_core.py"):
            for expected_symbol in (
                "class MetricsConfig",
                "class TracingConfig",
                "class LoggingConfig",
                "class EventConfig",
                "class ObservabilityCoreConfig",
                "class ObservabilityCore",
                "def increment_counter",
                "def export_metrics(",
                "def export_metrics_snapshot",
                "def span(",
                "def emit_event",
                "def health_check",
                "def get_runtime(",
            ):
                assert expected_symbol in contents, f"Vendor runtime missing {expected_symbol}"
        elif relative_path == Path("src/health/observability_core.py"):
            assert "def build_health_payload" in contents
            assert "def merge_metrics" in contents
        elif relative_path == Path(
            "src/modules/free/observability/core/observability_core_types.py"
        ):
            for expected_type in (
                "class ObservabilityEvent",
                "class ObservabilitySpan",
                "class ObservabilityMetricSnapshot",
                "class ObservabilitySummary",
                "class ObservabilityCoreResult",
            ):
                assert expected_type in contents
        elif relative_path == Path("nestjs/configuration.js"):
            assert "module.exports" in contents
            assert "loadConfiguration" in contents

    generator.generate_variant_files("fastapi", tmp_path, renderer, base_context)
    fastapi_config = tmp_path / "config" / "observability" / "observability_core.yaml"
    fastapi_integration = (
        tmp_path
        / "tests"
        / "modules"
        / "integration"
        / "observability"
        / "test_observability_core_integration.py"
    )
    fastapi_expected = {
        tmp_path / "src" / "modules" / "free" / "observability" / "core" / "observability_core.py",
        tmp_path / "src" / "health" / "observability_core.py",
        tmp_path
        / "src"
        / "modules"
        / "free"
        / "observability"
        / "core"
        / "routers"
        / "observability_core.py",
        fastapi_config,
        fastapi_integration,
    }
    for artefact in fastapi_expected:
        assert artefact.exists(), f"Expected FastAPI artefact {artefact}"
        contents = artefact.read_text().strip()
        assert contents, f"Generated FastAPI file {artefact} is empty"

        relative_path = artefact.relative_to(tmp_path)
        if relative_path == Path("src/modules/free/observability/core/observability_core.py"):
            assert "ObservabilityCoreConfig" in contents
            assert "def register_fastapi" in contents
            assert "app.include_router" in contents
        elif relative_path == Path("src/health/observability_core.py"):
            assert "def build_health_router" in contents
            assert "register_observability_core_health" in contents
        elif relative_path == Path(
            "src/modules/free/observability/core/routers/observability_core.py"
        ):
            for expected_route in (
                "def build_router",
                '@router.get("/health"',
                '@router.get("/metrics"',
                '@router.get("/metrics/raw"',
                '@router.get("/events"',
                '@router.post("/events"',
                '@router.get("/traces"',
            ):
                assert expected_route in contents, f"FastAPI router missing {expected_route}"
        elif relative_path == Path("config/observability/observability_core.yaml"):
            assert contents.startswith("# Default Observability configuration")
            assert "observability:" in contents
            assert "metrics:" in contents
            assert "tracing:" in contents
        elif relative_path == Path(
            "tests/modules/integration/observability/test_observability_core_integration.py"
        ):
            assert "pytest.mark.integration" in contents
            assert "register_fastapi" in contents
            assert "ObservabilityCoreConfig" in contents

    generator.generate_variant_files("nestjs", tmp_path, renderer, base_context)
    service_file = (
        tmp_path
        / "src"
        / "modules"
        / "free"
        / "observability"
        / "core"
        / "observability-core"
        / "observability-core.service.ts"
    )
    controller_file = (
        tmp_path
        / "src"
        / "modules"
        / "free"
        / "observability"
        / "core"
        / "observability-core"
        / "observability-core.controller.ts"
    )
    module_file = (
        tmp_path
        / "src"
        / "modules"
        / "free"
        / "observability"
        / "core"
        / "observability-core"
        / "observability-core.module.ts"
    )
    configuration_file = (
        tmp_path
        / "src"
        / "modules"
        / "free"
        / "observability"
        / "core"
        / "observability-core"
        / "observability-core.configuration.ts"
    )
    health_controller_file = tmp_path / "src" / "health" / "observability-core-health.controller.ts"
    health_module_file = tmp_path / "src" / "health" / "observability-core-health.module.ts"
    integration_spec = (
        tmp_path
        / "tests"
        / "modules"
        / "integration"
        / "observability"
        / "observability_core.integration.spec.ts"
    )

    for artefact in (
        service_file,
        controller_file,
        module_file,
        configuration_file,
        health_controller_file,
        health_module_file,
        integration_spec,
    ):
        assert artefact.exists(), f"Expected NestJS artefact {artefact}"
        contents = artefact.read_text().strip()
        assert contents, f"Generated NestJS file {artefact} is empty"

        if artefact == service_file:
            assert "class ObservabilityCoreService" in contents
            for expected_method in (
                "recordEvent",
                "recentEvents",
                "recordSpan",
                "recentSpans",
                "incrementCounter",
                "setGauge",
                "exportMetrics",
                "getSummary",
            ):
                assert expected_method in contents
        elif artefact == controller_file:
            assert (
                "@Controller('observability-core')" in contents
                or '@Controller("observability-core")' in contents
            ), "NestJS controller should declare observability-core route"
            for expected_endpoint in (
                "@Get('health')",
                "@Get('metrics')",
                "@Get('events')",
                "@Post('events')",
                "@Get('traces')",
            ):
                assert (
                    expected_endpoint in contents or expected_endpoint.replace("'", '"') in contents
                )
        elif artefact == module_file:
            assert "@Module" in contents
            assert "ObservabilityCoreController" in contents
            assert "ObservabilityCoreService" in contents
        elif artefact == configuration_file:
            assert "registerAs" in contents
            assert "observabilityCoreConfiguration" in contents or "observabilityCore" in contents
            assert "retryAttempts" in contents
        elif artefact == health_controller_file:
            assert (
                "@Controller('api/health/module')" in contents
                or '@Controller("api/health/module")' in contents
            )
            assert (
                "@Get('observability-core')" in contents or '@Get("observability-core")' in contents
            )
        elif artefact == health_module_file:
            assert "@Module" in contents
            assert "ObservabilityCoreModule" in contents
            assert "ObservabilityCoreHealthController" in contents
        elif artefact == integration_spec:
            assert "describe('ObservabilityCoreModule" in contents
            assert "get('/api/health/module/observability-core')" in contents
            assert "ObservabilityCoreService" in contents


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
        "templates/base/observability_core.py.j2",
        "templates/base/observability_core_health.py.j2",
        "templates/base/observability_core_types.py.j2",
        "templates/variants/fastapi/observability_core.py.j2",
        "templates/variants/fastapi/observability_core_routes.py.j2",
        "templates/variants/fastapi/observability_core_health.py.j2",
        "templates/variants/fastapi/observability_core_config.yaml.j2",
        "templates/variants/nestjs/observability_core.service.ts.j2",
        "templates/variants/nestjs/observability_core.controller.ts.j2",
        "templates/variants/nestjs/observability_core.module.ts.j2",
        "templates/variants/nestjs/observability_core.configuration.ts.j2",
        "templates/variants/nestjs/observability_core.health.controller.ts.j2",
        "templates/variants/nestjs/observability_core.health.module.ts.j2",
        "templates/vendor/nestjs/configuration.js.j2",
        "templates/tests/integration/test_observability_core_integration.j2",
        "templates/tests/integration/observability_core.integration.spec.ts.j2",
    ]
    for rel_path in expected:
        assert (module_root / rel_path).exists(), rel_path
