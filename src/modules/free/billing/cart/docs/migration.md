# Migration

This document captures upgrade guidance across Cart module releases.

## 1.0.0

- First stable release. Includes rewritten runtime, FastAPI adapter, and health surface.
- Previous draft scaffolds can be removed before installing this version—generated files are not
  backward compatible.
- Generated sources now live under `src/modules/free/billing/cart` to align with the unified module
  layout.

## Future Upgrades

- Monitor the changelog in `module.yaml` for deprecations. We follow semantic versioning—minor bumps
  indicate additive behaviour, major bumps signal breaking changes.
- Run `poetry run pytest tests/modules/free/billing/cart -q` after each upgrade to validate
  integrations.
- Re-run the generator per framework target to materialise updated templates.
