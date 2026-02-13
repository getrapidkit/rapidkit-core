# RapidKit Db Sqlite Module

SQLite database integration for development

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

- Provide a lightweight SQLite runtime facade with connection pooling, transactional helpers, and
  safe execution helpers (`execute`, `executemany`).
- Generate FastAPI wiring (router + registration helper) exposing:
  - `GET /db-sqlite/health` for health diagnostics.
  - `GET /db-sqlite/tables` for a quick schema snapshot.
- Generate NestJS wiring (service/controller/module) with a dedicated health module so teams can
  consume the same runtime surface in Node backends.
- Scaffold configuration defaults into `config/database/db_sqlite.yaml` and ship snippets for common
  settings/ENV layouts.
- Keep installs reproducible via vendor snapshots under `.rapidkit/vendor/...`.

______________________________________________________________________

## Install Commands

```bash
rapidkit add module db_sqlite
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
running the generator to bake defaults into emitted files (or edit `config/database/db_sqlite.yaml`
after generation).

| Environment Variable                      | Effect                                                                          |
| ----------------------------------------- | ------------------------------------------------------------------------------- |
| `RAPIDKIT_DB_SQLITE_PATH`                 | Default database path (e.g. `./.rapidkit/runtime/sqlite/app.db` or `:memory:`). |
| `RAPIDKIT_DB_SQLITE_CREATE_IF_MISSING`    | When `true`, create parent dirs / DB file if missing.                           |
| `RAPIDKIT_DB_SQLITE_TIMEOUT_SECONDS`      | Connection timeout in seconds (float).                                          |
| `RAPIDKIT_DB_SQLITE_POOL_MAX_SIZE`        | Max pooled connections (min 1).                                                 |
| `RAPIDKIT_DB_SQLITE_POOL_RECYCLE_SECONDS` | Recycle pooled connections after N seconds (0 disables).                        |
| `RAPIDKIT_DB_SQLITE_PRAGMAS`              | Extra PRAGMAs (JSON object or `key=value,key2=value2`).                         |

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
poetry run pytest tests/modules/free/database/db_sqlite -q

poetry run python scripts/check_module_integrity.py --module free/database/db_sqlite
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
