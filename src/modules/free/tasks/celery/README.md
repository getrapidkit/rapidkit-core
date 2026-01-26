# RapidKit Celery Module

Production-ready Celery task orchestration for asynchronous workloads

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

- Configurable Celery application builder with environment loading helpers.
- Vendor runtime snapshot exposing `CeleryAppConfig`, `create_celery_app`, and task registry
  utilities.
- FastAPI dependency wiring for injecting Celery apps and health routers.
- NestJS service that proxies Celery task dispatch via `celery-node`.
- Environment snippet provisioning broker and backend configuration.

______________________________________________________________________

## Install Commands

```bash
rapidkit add module celery
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

Key environment variables parsed by `load_config_from_env`:

| Variable                         | Default                    | Description                         |
| -------------------------------- | -------------------------- | ----------------------------------- |
| `RAPIDKIT_CELERY_BROKER_URL`     | `redis://localhost:6379/0` | Celery broker connection string     |
| `RAPIDKIT_CELERY_RESULT_BACKEND` | `redis://localhost:6379/1` | Result backend URI                  |
| `RAPIDKIT_CELERY_DEFAULT_QUEUE`  | `default`                  | Queue name used when none specified |
| `RAPIDKIT_CELERY_ENABLE_UTC`     | `true`                     | Toggles UTC handling                |
| `RAPIDKIT_CELERY_TIMEZONE`       | `UTC`                      | Timezone for scheduled tasks        |
| `RAPIDKIT_CELERY_IMPORTS`        | `apps.workers.tasks`       | Modules auto-imported by Celery     |
| `RAPIDKIT_CELERY_AUTODISCOVER`   | `apps.workers`             | Packages auto-discovered for tasks  |

Override hooks (`CeleryOverrides`) let enterprise users mutate configuration factories or
post-process the app instance.

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
poetry run pytest tests/modules/free/tasks/celery -q

poetry run python scripts/check_module_integrity.py --module free/tasks/celery
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
