# RapidKit Support Center Module

`support_center` provides a production-shaped support workflow boundary for customer operations,
marketplace delivery, license/download issues, entitlement reviews, and product-factory support
loops.

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

- Open tenant-aware support tickets with customer, requester, priority, tags, metadata, and SLA due
  time.
- Assign tickets to agents and move them through open, pending, resolved, and closed states.
- Store internal or public ticket notes with author and timestamp context.
- Detect SLA breaches for unresolved tickets.
- Capture audit events for ticket open, assignment, note, resolution, and closure.
- Generate FastAPI and NestJS project files plus a shared vendor runtime contract.

______________________________________________________________________

## Install Commands

```bash
rapidkit add module support_center
rapidkit reconcile
rapidkit modules lock --overwrite
```

______________________________________________________________________

## Directory Layout

| Path           | Responsibility                                                |
| -------------- | ------------------------------------------------------------- |
| `module.yaml`  | Canonical metadata, compatibility, dependencies, and docs map |
| `config/`      | Support workflow defaults and generated configuration         |
| `generate.py`  | Module generation entry point                                 |
| `frameworks/`  | FastAPI and NestJS framework adapters                         |
| `templates/`   | Vendor and framework-specific rendered assets                 |
| `overrides.py` | Optional runtime override hooks                               |
| `docs/`        | Reference documentation linked by `module.yaml`               |

______________________________________________________________________

## Generation Workflow

1. `module.yaml` is validated by the module structure checker.
1. Support workflow dependencies and shared contracts are resolved before rendering.
1. Vendor/runtime assets are rendered from templates.
1. The selected framework adapter maps generated files into project-relative paths.
1. Snippet contracts and module parity checks verify the generated surface.

______________________________________________________________________

## Runtime Customisation

| Environment Variable                        | Effect                                           |
| ------------------------------------------- | ------------------------------------------------ |
| `RAPIDKIT_SUPPORT_CENTER_ENABLED`           | Enables generated support workflow surfaces.     |
| `RAPIDKIT_SUPPORT_CENTER_DEFAULT_SLA_HOURS` | Default SLA due window for newly opened tickets. |
| `RAPIDKIT_SUPPORT_CENTER_AUDIT_MODE`        | Controls audit event forwarding.                 |

______________________________________________________________________

## Security & Audit

- Connect ticket audit events to account, order, entitlement, and download-token history.
- Use internal notes for support context that should not be exposed to customers.
- Keep ticket assignment separate from final resolution.
- Export SLA breach counts into observability dashboards before public launch.

______________________________________________________________________

## Testing Checklist

```bash
poetry run pytest tests/modules/free/business/support_center -q
poetry run python scripts/validate_module_structure.py free/business/support_center
poetry run python scripts/check_module_integrity.py --module free/business/support_center
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
