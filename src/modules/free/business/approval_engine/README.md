# RapidKit Approval Engine Module

`approval_engine` provides a production-shaped approval workflow boundary for admin, marketplace,
workflow, and product-factory actions.

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

- Register approval policies with allowed reviewer roles and optional escalation role.
- Require request and decision reasons before sensitive work proceeds.
- Capture immutable audit events for policy registration, request creation, approval, rejection,
  escalation, and cancellation.
- Keep tenant, actor, action, reviewer, and reason metadata attached to every approval path.
- Generate FastAPI and NestJS project files plus a shared vendor runtime contract.

______________________________________________________________________

## Install Commands

```bash
rapidkit add module approval_engine
rapidkit reconcile
rapidkit modules lock --overwrite
```

______________________________________________________________________

## Directory Layout

| Path           | Responsibility                                                |
| -------------- | ------------------------------------------------------------- |
| `module.yaml`  | Canonical metadata, compatibility, dependencies, and docs map |
| `config/`      | Approval policy defaults and generated configuration          |
| `generate.py`  | Module generation entry point                                 |
| `frameworks/`  | FastAPI and NestJS framework adapters                         |
| `templates/`   | Vendor and framework-specific rendered assets                 |
| `overrides.py` | Optional runtime override hooks                               |
| `docs/`        | Reference documentation linked by `module.yaml`               |

______________________________________________________________________

## Generation Workflow

1. `module.yaml` is validated by the module structure checker.
1. Approval dependencies and shared contracts are resolved before rendering.
1. Vendor/runtime assets are rendered from templates.
1. The selected framework adapter maps generated files into project-relative paths.
1. Snippet contracts and module parity checks verify the generated surface.

______________________________________________________________________

## Runtime Customisation

| Environment Variable                      | Effect                                                    |
| ----------------------------------------- | --------------------------------------------------------- |
| `RAPIDKIT_APPROVAL_ENGINE_ENABLED`        | Enables generated approval workflow surfaces.             |
| `RAPIDKIT_APPROVAL_ENGINE_DEFAULT_ROLE`   | Default reviewer role when a policy does not specify one. |
| `RAPIDKIT_APPROVAL_ENGINE_REQUIRE_REASON` | Keeps request and decision reasons mandatory.             |

______________________________________________________________________

## Security & Audit

- Treat policy changes as production configuration and review them through change control.
- Store generated audit events in append-only storage for compliance-sensitive flows.
- Keep approval reasons concise but specific enough to explain the human decision.
- Emit approval IDs into downstream audit records.

______________________________________________________________________

## Testing Checklist

```bash
poetry run pytest tests/modules/free/business/approval_engine -q
poetry run python scripts/validate_module_structure.py free/business/approval_engine
poetry run python scripts/check_module_integrity.py --module free/business/approval_engine
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
