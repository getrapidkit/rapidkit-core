# RapidKit Org Admin Console Module

`org_admin_console` provides organization-level administration for SaaS products.

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

- Create organizations with unique slugs and owner membership.
- Invite members with scoped roles and accept invitations into active memberships.
- Update member roles with validation against configured role policy.
- Update organization settings and record changed keys.
- Expose health and audit events for tenant governance.

______________________________________________________________________

## Install Commands

```bash
rapidkit add module org_admin_console
rapidkit reconcile
rapidkit modules lock --overwrite
```

______________________________________________________________________

## Directory Layout

| Path           | Responsibility                                                |
| -------------- | ------------------------------------------------------------- |
| `module.yaml`  | Canonical metadata, compatibility, dependencies, and docs map |
| `config/`      | Organization administration defaults and generated config     |
| `generate.py`  | Module generation entry point                                 |
| `frameworks/`  | FastAPI and NestJS framework adapters                         |
| `templates/`   | Vendor and framework-specific rendered assets                 |
| `overrides.py` | Optional runtime override hooks                               |
| `docs/`        | Reference documentation linked by `module.yaml`               |

______________________________________________________________________

## Generation Workflow

1. `module.yaml` is validated by the module structure checker.
1. Organization governance dependencies and shared contracts are resolved before rendering.
1. Vendor/runtime assets are rendered from templates.
1. The selected framework adapter maps generated files into project-relative paths.
1. Snippet contracts and module parity checks verify the generated surface.

______________________________________________________________________

## Runtime Customisation

Use runtime configuration and `overrides.py` to adapt organization governance without editing
generated vendor code.

Typical customisation points:

- allowed roles
- invitation expiry
- settings validation
- audit event forwarding

______________________________________________________________________

## Security & Audit

- Keep role updates auditable.
- Route high-risk changes through `approval_engine` when needed.
- Export organization settings changes to observability and support workflows.
- Treat tenant boundaries as a production security contract.

______________________________________________________________________

## Testing Checklist

```bash
poetry run pytest tests/modules/free/business/org_admin_console -q
poetry run python scripts/validate_module_structure.py free/business/org_admin_console
poetry run python scripts/check_module_integrity.py --module free/business/org_admin_console
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
