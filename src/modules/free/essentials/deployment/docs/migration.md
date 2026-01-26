# Deployment Module Migration Guide

Use this guide when upgrading between deployment module versions.

## Before Upgrading

1. Review the changelog in `src/modules/free/essentials/deployment/module.yaml`.
1. Regenerate vendor snapshots with the current version and commit the results.
1. Create a fresh branch dedicated to the upgrade.

## Upgrade Steps

1. Update the module reference (`rapidkit modules upgrade deployment`).
1. Regenerate vendor snapshots and project artefacts.
1. Compare changes in Makefiles, Dockerfiles, Compose files, and workflows.
1. Update project-specific overrides or snippets as required.

## Post-Upgrade Validation

- Run `poetry run pytest tests/modules/deployment -q`.
- Execute `rapidkit modules lock --overwrite` and verify the diff.
- Confirm the CI workflow executes end-to-end in the target environment.

## Rollback Strategy

If the upgrade introduces regressions, revert the branch or use the rollback instructions in
`module.yaml` (`uninstall` strategy with backup snapshots).
