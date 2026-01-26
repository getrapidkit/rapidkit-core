# Users Core Migration Notes

This document tracks upgrade guidance for teams consuming the Users Core module.

## Upgrading to 1.0.1

Release 1.0.1 refreshes metadata and documentation so the module reports accurate testing
requirements and lint status. When bumping from 1.0.0:

1. **Regenerate artefacts** – run the generator for each target framework so the updated metadata
   and docs land in your project tree:
   `poetry run python -m src.modules.free.users.users_core.generate fastapi .`
1. **Update runbooks** – adjust any internal instructions that previously referenced
   `tests/modules/free_users_users_core`. The maintained regression suite now lives under
   `tests/modules/free/users/core`.
1. **Run the regression suite** – execute `poetry run pytest tests/modules/free/users/core -q` to
   verify generator, overrides, CLI entrypoint, and plugin behaviour in your environment.

## Upgrading from 0.1.x to 1.0.0

The 1.0.0 milestone introduced framework plugins, environment-driven overrides, and expanded
documentation. Use this checklist when moving from the 0.1.x previews:

1. **Regenerate artefacts** – invoke the generator for each framework (`fastapi`, `nestjs`) so the
   new dependency hooks and health helpers materialise in your repository.
1. **Review overrides** – define the `RAPIDKIT_USERS_CORE_*` environment variables anywhere you need
   to toggle registration, email uniqueness, or pagination defaults. Absent values fall back to the
   previous defaults to preserve behaviour.
1. **Health registration** – ensure `register_users_core_health(app)` (or the module-specific
   helper) runs during application startup to expose telemetry at `/api/health/module/users-core`.
1. **CI coverage** – include the module regression suite in your pipeline if not already present:
   `poetry run pytest tests/modules/free/users/core -q`.

No breaking API changes were introduced across these releases; service method signatures and
repository protocols remain source-compatible.
