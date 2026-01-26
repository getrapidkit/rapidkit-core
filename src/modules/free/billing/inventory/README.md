# RapidKit Inventory Module

Inventory and pricing service backing Cart + Stripe

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

- Provide an in-memory inventory runtime with validation, pricing fields, and a clean service API
  (`InventoryService`) suitable for demos, tests, and as a starting point for persistence adapters.
- Support item upsert/list flows plus safe stock adjustments with explicit error types (404/409/422
  mapping in the FastAPI router).
- Generate FastAPI wiring (router + health helper) exposing:
  - `GET /inventory/health`
  - `GET /inventory/items`
  - `POST /inventory/items/{sku}`
  - `POST /inventory/items/{sku}/adjust`
- Generate NestJS wiring (service/controller/module) so Node backends get the same surface.
- Scaffold configuration defaults into `config/inventory.yaml` and ship snippets for common setup.

______________________________________________________________________

## Install Commands

```bash
rapidkit add module inventory
```

Re-run `rapidkit modules lock --overwrite` after adding or upgrading the module so downstream
projects capture the new snapshot.

### Quickstart

Follow the end-to-end walkthrough in `docs/usage.md`.

### Demo

Run the module demo harness:

```bash
python scripts/run_demo.py
```

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

`overrides.py` supports **generation-time** overrides via environment variables. Set them before
running the generator to bake defaults into emitted files (or edit `config/inventory.yaml` after
generation).

| Environment Variable                     | Effect                                         |
| ---------------------------------------- | ---------------------------------------------- |
| `RAPIDKIT_INVENTORY_DEFAULT_CURRENCY`    | Default currency (e.g. `USD`).                 |
| `RAPIDKIT_INVENTORY_ALLOW_BACKORDERS`    | Allow selling past available inventory (bool). |
| `RAPIDKIT_INVENTORY_ALLOW_NEGATIVE`      | Allow negative on-hand quantities (bool).      |
| `RAPIDKIT_INVENTORY_LOW_STOCK_THRESHOLD` | Threshold used by health/metrics (int).        |
| `RAPIDKIT_INVENTORY_RESERVATION_TTL`     | Reservation TTL in minutes (int).              |
| `RAPIDKIT_INVENTORY_METADATA`            | JSON object merged into defaults metadata.     |
| `RAPIDKIT_INVENTORY_WAREHOUSES`          | JSON object merged into warehouses map.        |
| `RAPIDKIT_INVENTORY_NOTIFICATIONS`       | JSON object merged into notification settings. |

______________________________________________________________________

## Security & Audit

This module ships as part of the RapidKit module ecosystem and is intended to be **audited** as a
unit:

- Use `scripts/modules_doctor.py` (or `rapidkit modules vet`) to validate structure and generator
  invariants.
- Use `rapidkit modules verify-all` to verify recorded hashes/signatures when running in release
  mode.

If you extend this module, keep the documentation updated with the security assumptions and any
threat model relevant to your deployment.

______________________________________________________________________

## Testing Checklist

```bash
poetry run pytest tests/modules/free/billing/inventory -q

poetry run python scripts/check_module_integrity.py --module free/billing/inventory
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

For additional help, open an issue at <https://github.com/getrapidkit/core/issues> or consult the
full product documentation at <https://docs.rapidkit.top>.
