# RapidKit Deployment Module

Deployment tooling for RapidKit services.

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

- Golden Dockerfile, docker-compose, and Makefile scaffolding for Python and Node runtimes
- Modular Compose overlays in `deploy/compose/` for local development and production releases
- GitHub Actions workflow template with optional CI toggle baked into the generator context
- Vendor snapshots published under `.rapidkit/vendor/deployment/<version>` for reproducible builds
- Framework plug-in model mirroring the settings module, enabling additional adapters over time
- Snippet injection pipeline so kits can augment generated assets without forking templates

______________________________________________________________________

## Install Commands

```bash
rapidkit add module deployment
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

`overrides.py` exposes environment-controlled hooks so teams can tweak generated assets without
forking templates:

| Environment Variable                   | Effect                                                                    |
| -------------------------------------- | ------------------------------------------------------------------------- |
| `RAPIDKIT_DEPLOYMENT_SKIP_CI`          | Skip CI workflow generation (forces `include_ci=False` in render context) |
| `RAPIDKIT_DEPLOYMENT_FORCE_RUNTIME`    | Override detected runtime for project-level outputs (`python` or `node`)  |
| `RAPIDKIT_DEPLOYMENT_INCLUDE_POSTGRES` | Enable Postgres services irrespective of module defaults                  |
| `RAPIDKIT_DEPLOYMENT_EXTRA_WORKFLOW`   | Path to an additional workflow template appended post generation          |

See `DeploymentOverrides` for implementation details and extension points.

### Environment & Secrets Management

- Populate `.env` or `.env.local` with non-sensitive defaults; they are mounted automatically by the
  Compose overlays.
- Store production credentials outside of version control (for example in a password manager or
  secrets backend) and inject them at runtime via CI/CD or `docker compose --env-file` overrides.
- The generated `.dockerignore` keeps `.env` files out of Docker build contexts unless explicitly
  whitelisted.

### Compose Profiles

- `deploy/compose/base.yml` holds shared service definitions (images, health checks, volumes).
- `deploy/compose/local.yml` adds developer conveniences: live reload, bind mounts, and exposed
  ports.
- `deploy/compose/production.yml` enables hardened settings suitable for previews or production
  (restart policy, non-reload command).
- The Makefile exposes helpers that merge these overlays (`make docker-up`, `make docker-up-prod`).

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
poetry run pytest tests/modules/free/essentials/deployment -q

poetry run python scripts/check_module_integrity.py --module free/essentials/deployment
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
