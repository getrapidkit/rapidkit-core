# Module ↔ Kit Compatibility Matrix

This matrix summarizes the declared compatibility between free RapidKit modules and the officially
shipped kit profiles. Compatibility data is sourced from `src/modules/free/modules.yaml` under the
`kit_support` section and is surfaced by the `rapidkit add module` command during installation.

Note: Dependency resolution and install ordering are driven by each module's `module.yaml`
(`depends_on`), not by the tier catalog.

## Status Legend

- **supported** – Full support with automated overrides and tests.
- **experimental** – Works in internal testing, but expect rough edges; manual validation
  recommended.
- **planned** – Support is on the roadmap but not yet implemented.
- **unsupported** – No current plans or the module depends on features missing from the kit.

## Free Modules

| Module           | fastapi.standard | nestjs.standard | Notes                                                                     |
| ---------------- | ---------------- | --------------- | ------------------------------------------------------------------------- |
| settings         | ✅ supported     | ⚠️ experimental | Validated overrides for FastAPI; NestJS scaffolding undergoing hardening. |
| logging          | ✅ supported     | 🗓️ planned      | Logging pipeline will be ported after NestJS middleware audit.            |
| security_headers | ✅ supported     | ✅ supported    | FastAPI middleware and NestJS service share the same hardened defaults.   |
| db_postgres      | ✅ supported     | ✅ supported    | Ships async SQLAlchemy runtime plus NestJS pool service and health APIs.  |
| db_sqlite        | ✅ supported     | ❌ unsupported  | Focused on FastAPI dev workflows.                                         |
| redis            | ✅ supported     | ✅ supported    | Includes NestJS cache service, controller, and validation snippets.       |
| monitoring       | ✅ supported     | 🗓️ planned      | NestJS health endpoints being finalized.                                  |
| auth             | ✅ supported     | 🗓️ planned      | Requires NestJS passport integration.                                     |
| users            | ✅ supported     | ❌ unsupported  | Relies on FastAPI-specific scaffolding.                                   |
| billing          | ⚠️ experimental  | ❌ unsupported  | Stripe flow stable on FastAPI; NestJS implementation unscoped.            |
| notifications    | ⚠️ experimental  | 🗓️ planned      | Multi-channel delivery slated for NestJS Q4 release.                      |

> Keep compatibility notes in sync when updating `kit_support` metadata so the CLI and documentation
> stay aligned.
