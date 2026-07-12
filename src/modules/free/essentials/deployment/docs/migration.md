# Deployment Module Migration Guide

Use this guide when upgrading between deployment module versions.

## Before Upgrading

1. Review the changelog in `src/modules/free/essentials/deployment/module.yaml`.
1. Refresh the project lock with `rapidkit modules lock --overwrite`.
1. Verify the clean-clone path with `rapidkit modules restore --locked --ci --plan`.
1. Create a fresh branch dedicated to the upgrade.

## Upgrade Steps

1. Update the module reference (`rapidkit modules upgrade deployment`).
1. Regenerate project artefacts and refresh `.rapidkit/modules.lock.yaml`.
1. Compare changes in Makefiles, Dockerfiles, Compose files, and workflows.
1. Update project-specific overrides or snippets as required.

## Post-Upgrade Validation

- Run `poetry run pytest tests/modules/deployment -q`.
- Execute `rapidkit modules lock --overwrite` and verify the diff.
- Execute `rapidkit modules restore --locked --ci --plan` to prove cloneable restores still work.
- Confirm the CI workflow executes end-to-end in the target environment.

## Rollback Strategy

If the upgrade introduces regressions, revert the branch or use the rollback instructions in
`module.yaml` (`uninstall` strategy with backup snapshots).
