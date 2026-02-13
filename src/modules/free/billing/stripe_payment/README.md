# RapidKit Stripe Payment Module

Stripe payments and subscriptions

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

- In-memory Stripe facade that exposes health status, billing defaults, retry policy, webhook
  wiring, and feature flags for diagnostics.
- Framework adapters for FastAPI and NestJS that generate `/stripe-payment/health` and
  `/stripe-payment/metadata` endpoints with identical payloads.
- Environment-aware overrides that honour `RAPIDKIT_STRIPE_API_KEY`,
  `RAPIDKIT_STRIPE_WEBHOOK_SECRET`, and other toggles during generation.
- Snippet catalog for common Stripe workflows (customer portal webhook handlers, enhanced retries)
  that is injected into the generated metadata document.

______________________________________________________________________

## Install Commands

```bash
rapidkit add module stripe_payment
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

| Environment Variable                        | Effect                                                                                |
| ------------------------------------------- | ------------------------------------------------------------------------------------- |
| `RAPIDKIT_STRIPE_API_KEY`                   | Marks `environment.has_api_key` as true so health checks reflect secret availability. |
| `RAPIDKIT_STRIPE_WEBHOOK_SECRET`            | Marks `environment.has_webhook_secret` as true and informs webhook diagnostics.       |
| `RAPIDKIT_STRIPE_MODE`                      | Overrides the default billing mode (`test` or `live`).                                |
| `RAPIDKIT_STRIPE_DEFAULT_CURRENCY`          | Replaces the generated default currency code.                                         |
| `RAPIDKIT_STRIPE_STATEMENT_DESCRIPTOR`      | Sets the descriptor used across metadata payloads.                                    |
| `RAPIDKIT_STRIPE_AUTOMATIC_PAYMENT_METHODS` | Enables or disables automatic payment methods in health snapshots.                    |
| `RAPIDKIT_STRIPE_MAX_RETRIES`               | Raises or lowers retry policy `max_attempts` during generation.                       |

All overrides are applied consistently to FastAPI and NestJS outputs.

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
poetry run pytest tests/modules/free/billing/stripe_payment -q

poetry run python scripts/check_module_integrity.py --module free/billing/stripe_payment
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

For additional help, open an issue at <https://github.com/getrapidkit/rapidkit-core/issues> or
consult the full product documentation at <https://docs.rapidkit.top>.
