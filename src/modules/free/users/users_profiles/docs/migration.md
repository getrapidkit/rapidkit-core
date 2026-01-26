# Users Profiles Module Migration Guide

Use this document to track changes between module releases and plan safe upgrades.

## Upgrading to 1.0.1

Release 1.0.1 refreshes module metadata and documentation so test orchestration matches the live
suite. When adopting the patch:

1. **Regenerate artefacts** – execute the generator for each target framework to pick up the
   metadata adjustments:
   `poetry run python -m src.modules.free.users.users_profiles.generate fastapi .`
1. **Update runbooks** – switch any documentation or CI jobs that referenced
   `tests/modules/free_users_users_profiles` to the maintained path
   `tests/modules/free/users/profiles`.
1. **Run regression suite** – execute `poetry run pytest tests/modules/free/users/profiles -q` to
   confirm generator, override, CLI, and plugin behaviour.

## Upgrading from 0.1.x to 1.0.0

Version 1.0.0 introduced the unified generator, simultaneous FastAPI/NestJS support, and an
in-memory repository for demos. When moving from the preview releases:

1. Regenerate the module for each target (`fastapi` and/or `nestjs`).
1. Inspect generated runtime and repository signatures for local customisations.
1. Re-run the regression suite: `poetry run pytest tests/modules/free/users/profiles -q`.
1. Validate the health endpoint continues to respond at `/api/health/module/users_profiles`.

Document additional migration notes below as new versions ship.
