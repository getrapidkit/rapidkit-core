# RapidKit Connector Pack Library Module

`connector_pack_library` provides a provider connector catalog for automation and marketplace
products.

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

- Register connector packs with provider, display name, scopes, and metadata.
- Install connector packs per tenant or product context.
- Mark connector health as installed or degraded.
- Track credential rotation with required reasons.
- List packs by provider or status and expose audit history.

______________________________________________________________________

## Install Commands

```bash
rapidkit add module connector_pack_library
rapidkit reconcile
rapidkit modules lock --overwrite
```

______________________________________________________________________

## Directory Layout

| Path           | Responsibility                                                |
| -------------- | ------------------------------------------------------------- |
| `module.yaml`  | Canonical metadata, compatibility, dependencies, and docs map |
| `config/`      | Connector catalog defaults and generated configuration        |
| `generate.py`  | Module generation entry point                                 |
| `frameworks/`  | FastAPI and NestJS framework adapters                         |
| `templates/`   | Vendor and framework-specific rendered assets                 |
| `overrides.py` | Optional runtime override hooks                               |
| `docs/`        | Reference documentation linked by `module.yaml`               |

______________________________________________________________________

## Generation Workflow

1. `module.yaml` is validated by the module structure checker.
1. Connector catalog dependencies and shared contracts are resolved before rendering.
1. Vendor/runtime assets are rendered from templates.
1. The selected framework adapter maps generated files into project-relative paths.
1. Snippet contracts and module parity checks verify the generated surface.

______________________________________________________________________

## Runtime Customisation

Use runtime configuration and `overrides.py` to adapt connector pack behavior without editing
generated vendor code.

Typical customisation points:

- allowed connector providers
- required scopes
- credential rotation policy
- degraded health routing

______________________________________________________________________

## Security & Audit

- Treat connector scopes as a permission boundary.
- Require credential rotation reasons and audit every rotation.
- Route degraded connector health into support and incident workflows.
- Keep provider-specific adapters behind explicit connector pack records.

______________________________________________________________________

## Testing Checklist

```bash
poetry run pytest tests/modules/free/business/connector_pack_library -q
poetry run python scripts/validate_module_structure.py free/business/connector_pack_library
poetry run python scripts/check_module_integrity.py --module free/business/connector_pack_library
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
