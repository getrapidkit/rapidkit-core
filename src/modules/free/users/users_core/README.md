# RapidKit Users Core Module

Opinionated domain services and HTTP adapters for managing RapidKit users

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

- **Domain modelling** – ships Pydantic DTOs plus dataclasses that capture identity, profile, and
  status metadata with validation ready for HTTP transport.
- **Service orchestration** – `UsersService` coordinates create, retrieve, update, and search
  operations while `UsersServiceFacade` exposes ergonomics for endpoints, jobs, and CLIs.
- **Repository abstraction** – a protocol defines persistence behaviour; the in-memory
  implementation supports local development, and teams can register custom repositories without
  touching templates.
- **Cross-framework adapters** – FastAPI dependency helpers/routers and NestJS providers expose the
  same service contract to each framework with minimal glue.
- **Health telemetry** – module health registration surfaces `/api/health/module/users-core` so
  observability dashboards can detect configuration drift early.

______________________________________________________________________

## Install Commands

```bash
rapidkit add module users_core
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

Environment variables surface through `UsersServiceSettings` and the overrides mixin:

| Environment Variable                         | Effect                                                              |
| -------------------------------------------- | ------------------------------------------------------------------- |
| `RAPIDKIT_USERS_CORE_ALLOW_REGISTRATION`     | Enable or disable self-service onboarding flows.                    |
| `RAPIDKIT_USERS_CORE_ENFORCE_UNIQUE_EMAIL`   | Enforce unique email addresses at the service layer.                |
| `RAPIDKIT_USERS_CORE_DEFAULT_LOCALE`         | Set the fallback locale for notifications and audit logs.           |
| `RAPIDKIT_USERS_CORE_AUDIT_LOG_ENABLED`      | Toggle structured audit event emission for create/update.           |
| `RAPIDKIT_USERS_CORE_MAX_RESULTS_PER_PAGE`   | Control default pagination size for directory searches (preferred). |
| `RAPIDKIT_USERS_CORE_MAX_RESULTS`            | Legacy name for default page size; still supported as a fallback.   |
| `RAPIDKIT_USERS_CORE_PASSWORDLESS_SUPPORTED` | Advertise passwordless capability to clients.                       |

Register custom repositories or service subclasses via `configure_users_dependencies()` to extend
behaviour without patching generated code.

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
poetry run pytest tests/modules/free/users/users_core -q

poetry run python scripts/check_module_integrity.py --module free/users/users_core
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
