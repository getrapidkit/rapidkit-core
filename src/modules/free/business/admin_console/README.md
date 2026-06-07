# RapidKit Admin Console Module

`admin_console` provides a reusable admin action surface for generated products.

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

- Register admin actions with required roles, dangerous-action flags, and reason policy.
- Execute actions through a stable handler contract.
- Capture run status, actor, tenant, reason, result, and error context.
- Summarize actions, runs, failed runs, and dangerous operations.
- Generate FastAPI and NestJS project files plus a shared vendor runtime.

______________________________________________________________________

## Install Commands

```bash
rapidkit add module admin_console
rapidkit reconcile
rapidkit modules lock --overwrite
```

______________________________________________________________________

## Directory Layout

| Path           | Responsibility                                                |
| -------------- | ------------------------------------------------------------- |
| `module.yaml`  | Canonical metadata, compatibility, dependencies, and docs map |
| `config/`      | Declarative generation/runtime configuration                  |
| `generate.py`  | Module generation entry point                                 |
| `frameworks/`  | FastAPI and NestJS framework adapters                         |
| `templates/`   | Vendor and framework-specific rendered assets                 |
| `overrides.py` | Optional runtime override hooks                               |
| `docs/`        | Reference documentation linked by `module.yaml`               |

______________________________________________________________________

## Generation Workflow

1. `module.yaml` is validated by the module structure checker.
1. Dependencies are resolved before this module is materialized into the target project.
1. Vendor/runtime assets are rendered from templates.
1. The selected framework adapter maps generated files into project-relative paths.
1. Snippet contracts and module parity checks verify the generated surface.

______________________________________________________________________

## Runtime Customisation

Use runtime configuration and `overrides.py` to adapt admin action behavior without editing
generated vendor code.

Typical customisation points:

- action role policy
- dangerous action reason requirements
- run history persistence
- support or incident routing for failed runs

______________________________________________________________________

## Security & Audit

- Treat dangerous admin actions as privileged operations.
- Require reasons for publish, archive, import, entitlement, and billing actions.
- Store run history in append-only audit storage for production workflows.
- Route failed runs into support or incident workflows.

______________________________________________________________________

## Testing Checklist

```bash
poetry run pytest tests/modules/free/business/admin_console -q
poetry run python scripts/validate_module_structure.py free/business/admin_console
poetry run python scripts/check_module_integrity.py --module free/business/admin_console
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
