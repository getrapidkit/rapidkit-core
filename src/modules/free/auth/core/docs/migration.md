# Auth Core Migration Guide

This page records the key steps required to move between released versions of the Auth Core module.
Follow the relevant section when you bump the module version in `module.yaml` or upgrade an existing
project.

## 0.1.0 → 0.1.1

Version 0.1.1 introduced structured overrides, repository level tests, and documentation updates. To
upgrade from the initial preview release:

1. Re-run the generator for each framework target so the latest templates are rendered:

   ```bash
   poetry run python -m src.modules.free.auth.core.generate fastapi .
   poetry run python -m src.modules.free.auth.core.generate nestjs ./tmp/auth-core-nest
   ```

1. Compare the generated overrides in `src/modules/free/auth/core/overrides.py` with any project
   specific customisations. Migrate your logic into the new `AuthCoreOverrides` hooks.

1. Review the new environment variables introduced in the README. Set `RAPIDKIT_AUTH_CORE_POLICY` if
   you previously handled password requirements manually.

1. Run the updated test suite:

   ```bash
   poetry run pytest tests/modules/free_auth_core -q
   ```

1. Validate the health endpoint JSON includes a `pepper_configured` flag. This is now surfaced to
   give operators easy visibility into configuration drift.

## Performing Safe Upgrades

- Always regenerate vendor artefacts into a temporary directory first and review the diff before
  applying the changes to your live project.
- Pay attention to changes under `.rapidkit/vendor/auth_core/<version>`. They represent the
  canonical runtime logic that the module relies on.
- Use feature flags or staged deployments when altering hashing parameters so you can monitor login
  failure rates.
- If you expose Auth Core functionality through public APIs, review any schema changes documented in
  the changelog before shipping to production.
