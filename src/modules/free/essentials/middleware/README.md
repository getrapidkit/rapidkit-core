# RapidKit Middleware Module

HTTP middleware pipeline with FastAPI and NestJS support.

This README follows the shared RapidKit module format:

1. **Overview & capabilities**
1. **Installation commands**
1. **Directory layout**
1. **Generation workflow**
1. **Runtime customisation hooks**
1. **Testing & release checklist**
1. **Reference links**

Use the same headings when documenting other modules so maintainers know what to expect.

As a RapidKit module, this module also follows the shared metadata/documentation standard:

- `module.yaml` is the canonical source of truth (including the `documentation:` map).
- Module docs live under `docs/` and should match the keys referenced from `module.yaml`.
- The module changelog is maintained in `docs/changelog.md` and referenced both from `module.yaml`
  and this README.

______________________________________________________________________

## Module Capabilities

- **ProcessTimeMiddleware** tracks request duration and adds `X-Process-Time` response header
- **ServiceHeaderMiddleware** identifies services via `X-Service` header for distributed tracing
- Custom header framework with decorator-based registration for extensibility
- Pre-configured CORS middleware template (disabled by default, easily enabled)
- Dedicated health endpoint (`/api/health/module/middleware`) for monitoring and observability
- Vendor snapshots published under `.rapidkit/vendor/middleware/<version>` for reproducible builds
- Framework plug-in model enabling FastAPI and NestJS support with consistent behaviour
- Comprehensive integration test suite (15+ tests) generated alongside middleware code

______________________________________________________________________

## Install Commands

```bash
rapidkit add module middleware
```

Re-run `rapidkit modules lock --overwrite` after adding or upgrading the module so downstream
projects capture the new snapshot.

### Quickstart

Follow the end-to-end walkthrough in `docs/usage.md`.

______________________________________________________________________

## Directory Layout

| Path               | Responsibility                                                              |
| ------------------ | --------------------------------------------------------------------------- |
| `module.yaml`      | Canonical metadata (version, compatibility, documentation map)              |
| `config/base.yaml` | Declarative spec that drives prompts and dependency resolution              |
| `generate.py`      | CLI/automation entry point for rendering vendor and project variants        |
| `frameworks/`      | Framework plugin implementations registered via `modules.shared.frameworks` |
| `overrides.py`     | Runtime opt-in hooks applied via environment variables                      |
| `docs/`            | Module docs referenced from `module.yaml` (usage/overview/changelog)        |
| `templates/`       | Base templates plus per-framework variants                                  |

______________________________________________________________________

## Generation Workflow

1. `generate.py` loads `module.yaml` and checks version drift with
   `modules.shared.versioning.ensure_version_consistency`.
1. Vendor artefacts are rendered from templates into `.rapidkit/vendor/...` for reproducible
   installs.
1. The requested framework plugin maps templates into project-relative paths.
1. Optional lifecycle hooks (`pre_generation_hook`, `post_generation_hook`) handle final
   adjustments.

______________________________________________________________________

## Runtime Customisation

`overrides.py` exposes environment-controlled hooks so teams can tweak generated middleware without
forking templates:

| Environment Variable               | Effect                                                                |
| ---------------------------------- | --------------------------------------------------------------------- |
| `RAPIDKIT_MIDDLEWARE_ENABLE_CORS`  | Enable CORS middleware in generated code (forces `cors_enabled=True`) |
| `RAPIDKIT_MIDDLEWARE_PROCESS_TIME` | Control process time header (forces `process_time_header` setting)    |
| `RAPIDKIT_MIDDLEWARE_SERVICE_NAME` | Override service name for `X-Service` header in render context        |

See `MiddlewareOverrides` for implementation details and extension points. Custom middleware can be
added by editing the generated `middleware.py` file or extending the override hooks.

______________________________________________________________________

## Demo And Smoke Checks

Use the module demo runner to inspect generated output before promoting template changes:

```bash
python scripts/run_demo.py fastapi
python scripts/run_demo.py nestjs
```

For release validation, compare the generated FastAPI and NestJS projects with the module's expected
outputs, then run the module-scoped test and validator commands in the testing checklist below.

______________________________________________________________________

## Security & Audit

- Treat request headers as untrusted input; only propagate correlation headers after normalization.
- Keep CORS disabled by default and scope origins/methods/headers explicitly in production.
- Do not expose internal service names or tenant identifiers through response headers unless they
  are approved for external clients.
- Record middleware configuration changes with actor, reason, target environment, and rollback
  version.

Use `scripts/modules_doctor.py` or `rapidkit modules verify-all` before release to validate
structure, generated assets, and recorded hashes/signatures.

If you extend this module, keep the documentation updated with the security assumptions and any
threat model relevant to your deployment.

______________________________________________________________________

## Enterprise Operations

| Area        | Production expectation                                                                                       |
| ----------- | ------------------------------------------------------------------------------------------------------------ |
| Ownership   | Assign platform/API ownership for middleware order, header policy, and CORS changes.                         |
| Metrics     | Track request counts, latency percentiles, error rates, rejected origins, and missing correlation IDs.       |
| Audit       | Capture operator, reason, previous value, new value, environment, and correlation ID for config changes.     |
| Idempotency | Keep middleware registration deterministic so repeated startup or module installs do not duplicate behavior. |
| Rollback    | Preserve the previous generated middleware config and module snapshot before changing header/CORS policy.    |

## Failure Modes

- Invalid CORS policy: fail closed for external origins and emit a clear health/configuration
  signal.
- Duplicate middleware registration: verify headers are emitted once and request latency remains
  bounded.
- Missing correlation ID: add a deterministic fallback and surface the rate as telemetry.
- Downstream exception: middleware must propagate the exception while preserving observable timing
  behavior when possible.
- Configuration drift: rerun generator smoke checks and compare `.rapidkit/vendor` output before
  publishing.

______________________________________________________________________

## Testing Checklist

```bash
poetry run pytest tests/modules/free/essentials/middleware -q

poetry run python scripts/check_module_integrity.py --module free/essentials/middleware
poetry run python scripts/validate_module_readme_standard.py --module free/essentials/middleware
poetry run python scripts/validate_module_docs_quality.py --module free/essentials/middleware
poetry run python scripts/validate_module_snippet_configs.py --module free/essentials/middleware
```

______________________________________________________________________

## Release Checklist

1. Update templates and/or `module.yaml`.
1. Regenerate vendor snapshots and project variants for every supported framework.
1. Inspect rendered files (`.rapidkit/vendor` and sample project outputs) for accuracy.
1. Execute the testing checklist above; ensure versioning is bumped when content hashes change.
1. Commit regenerated assets alongside the updated metadata.

______________________________________________________________________

## Reference Documentation

- Overview: `docs/overview.md`
- Usage guide: `docs/usage.md`
- Advanced scenarios: `docs/advanced.md`
- Monitoring: `docs/monitoring.md`
- Changelog: `docs/changelog.md`
- Migration playbook: `docs/migration.md`
- Troubleshooting: `docs/troubleshooting.md`
- API reference: `docs/api-reference.md`
- Override contracts: `overrides.py`

For additional help, open an issue at <https://github.com/rapidkitlabs/rapidkit-core/issues> or
consult the full product documentation at <https://docs.rapidkit.top>.
