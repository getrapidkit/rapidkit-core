# Migration

This module is currently in the `0.x` series. While it is marked `stable` in the module manifest,
minor releases may still introduce breaking changes as the surface evolves.

## Upgrade checklist

1. Upgrade the module and refresh the lockfile:

   ```bash
   rapidkit add module observability_core
   rapidkit modules lock --overwrite
   ```

1. Re-run the generator for each framework variant you ship:

   ```bash
   poetry run python -m src.modules.free.observability.core.generate fastapi .
   poetry run python -m src.modules.free.observability.core.generate nestjs ./examples/observability-core-nest
   ```

1. Review `docs/changelog.md` for behavioural changes.

1. Smoke test the HTTP surface (`/health`, `/metrics`, `/events`, `/traces`).

## Configuration compatibility

- Prefer keeping custom defaults in your project config
  (`config/observability/observability_core.yaml`).
- If you use generation-time overrides, document them in your deployment runbooks so upgrades remain
  reproducible.
