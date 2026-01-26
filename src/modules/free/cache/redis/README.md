# RapidKit Redis Module

Unified Redis cache integration

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

- Async and sync Redis clients with retry/backoff logic, health probes, and FastAPI lifespan wiring.
- Sanitised metadata snapshots for dashboards and health endpoints via `get_redis_metadata`.
- Vendor-managed runtime stored under `.rapidkit/vendor` with thin project wrappers for rapid
  upgrades.
- NestJS configuration module, Joi validation schema, and injectable service exposing Redis
  defaults.
- Snippet catalogue injecting environment variables, health probes, and Pydantic settings fields.
- Override contract enabling environment-driven default mutations and optional snippet injection.

______________________________________________________________________

## Install Commands

```bash
rapidkit add module redis
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

| Environment Variable                                     | Effect                                                                     |
| -------------------------------------------------------- | -------------------------------------------------------------------------- |
| `RAPIDKIT_REDIS_FORCE_URL`                               | Override the resolved Redis connection URL.                                |
| `RAPIDKIT_REDIS_FORCE_HOST` / `PORT` / `DB` / `PASSWORD` | Mutate individual URL components when URL is derived dynamically.          |
| `RAPIDKIT_REDIS_FORCE_TLS`                               | Force TLS scheme regardless of configuration defaults.                     |
| `RAPIDKIT_REDIS_FORCE_PRECONNECT`                        | Toggle FastAPI lifespan preconnect handling.                               |
| `RAPIDKIT_REDIS_FORCE_RETRIES` / `BACKOFF` / `TTL`       | Adjust retry behaviour and cache TTL defaults.                             |
| `RAPIDKIT_REDIS_PROJECT_NAME`                            | Override project name/slug used in generated files.                        |
| `RAPIDKIT_REDIS_EXTRA_SNIPPET{,_DEST,_VARIANTS}`         | Copy an additional artefact after variant generation (see `overrides.py`). |

### Diagnostics Helpers

- Call `get_redis_metadata()` to inspect the resolved connection URL, retry policy, and cache TTL.
- The FastAPI health route (`/api/health/module/redis`) returns the same sanitised payload.

Refer to `overrides.py` for the full override matrix and behaviour.

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
poetry run pytest tests/modules/free/cache/redis -q

poetry run python scripts/check_module_integrity.py --module free/cache/redis
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
