# RapidKit Analytics Dashboard Module

`analytics_dashboard` provides a lightweight analytics dashboard runtime for generated products.

This README follows the shared RapidKit module format:

1. **Overview & capabilities**
1. **Installation commands**
1. **Directory layout**
1. **Generation workflow**
1. **Runtime customisation hooks**
1. **Testing & release checklist**
1. **Reference links**

As a RapidKit module, this module also follows the shared metadata/documentation standard:

- `module.yaml` is the canonical source of truth.
- Module docs live under `docs/` and should match the keys referenced from `module.yaml`.
- The module changelog is maintained in `docs/changelog.md`.

______________________________________________________________________

## Module Capabilities

- Record named metric points with Decimal-safe values and dimensions.
- Add dashboard widgets with visualization type and filters.
- Summarize metrics by count, total, average, min, and max.
- Drill down into metric points by dimensions.
- Capture dashboard snapshots for reporting and audit-ready review.

______________________________________________________________________

## Install Commands

```bash
rapidkit add module analytics_dashboard
rapidkit reconcile
rapidkit modules lock --overwrite
```

______________________________________________________________________

## Directory Layout

| Path           | Responsibility                                                |
| -------------- | ------------------------------------------------------------- |
| `module.yaml`  | Canonical metadata, compatibility, dependencies, and docs map |
| `config/`      | Analytics dashboard defaults and generated configuration      |
| `generate.py`  | Module generation entry point                                 |
| `frameworks/`  | FastAPI and NestJS framework adapters                         |
| `templates/`   | Vendor and framework-specific rendered assets                 |
| `overrides.py` | Optional runtime override hooks                               |
| `docs/`        | Reference documentation linked by `module.yaml`               |

______________________________________________________________________

## Generation Workflow

1. `module.yaml` is validated by the module structure checker.
1. Observability dependencies and shared contracts are resolved before rendering.
1. Vendor/runtime assets are rendered from templates.
1. The selected framework adapter maps generated files into project-relative paths.
1. Snippet contracts and module parity checks verify the generated surface.

______________________________________________________________________

## Runtime Customisation

Use runtime configuration and `overrides.py` to adapt dashboard behavior without editing generated
vendor code.

Typical customisation points:

- metric retention
- allowed dimensions
- widget defaults
- snapshot export policy

______________________________________________________________________

## Security & Audit

- Keep tenant, plan, product, and feature dimensions attached to product metrics.
- Use snapshots for admin review, customer reporting, and readiness dashboards.
- Connect dashboard output to observability storage before public launch.
- Avoid leaking sensitive customer data into dashboard dimensions.

______________________________________________________________________

## Testing Checklist

```bash
poetry run pytest tests/modules/free/observability/analytics_dashboard -q
poetry run python scripts/validate_module_structure.py free/observability/analytics_dashboard
poetry run python scripts/check_module_integrity.py --module free/observability/analytics_dashboard
```

______________________________________________________________________

## Release Checklist

1. Update templates and/or `module.yaml`.
1. Regenerate vendor snapshots and project variants for every supported framework.
1. Run the testing checklist.
1. Run module parity and product score checks.
1. Commit regenerated assets alongside metadata and documentation updates.

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
