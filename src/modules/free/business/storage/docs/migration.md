# Migration Guide

The Storage module has not introduced breaking changes since the 1.0.0 release.

## Upgrading Within 1.x

- Review the changelog in `module.yaml` for each release.
- Re-run the generator for your target framework to pick up template improvements.
- If you maintain S3/GCS overrides, diff your custom adapter implementations against the latest
  scaffolds under `templates/snippets/`.
- Re-run the module structure validator and the pytest suite after upgrading.

## Future Changes

Significant updates (for example, first-party cloud adapters) will include step-by-step migration
guidance here. Subscribe to release notes or watch the repository to be notified.
