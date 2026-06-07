# RapidKit Core Developer Guide

Last updated: 2026-06-04

This guide is for contributors working on the RapidKit core engine, free module catalog, release
kits, and distribution automation.

## Requirements

| Tool    | Recommended                           |
| ------- | ------------------------------------- |
| Python  | 3.10.x                                |
| Poetry  | Latest stable                         |
| Node.js | 20.x for NestJS gates                 |
| npm     | Latest stable compatible with Node 20 |
| Git     | 2.40+                                 |

## Setup

```bash
git clone https://github.com/rapidkitlabs/rapidkit-core.git rapidkit-core
cd rapidkit-core
poetry install
poetry run pre-commit install
```

If you are working from the internal monorepo checkout, run commands from the `core/` directory.

## Core Concepts

- Modules live under `src/modules/free/<category>/<slug>`.
- Kits live under `src/kits`.
- Distribution file maps decide what ships in the public package.
- `dev-engine/playbooks` contains the current operating guidance.
- `dev-engine/audit-history` is the active evidence root.

## Everyday Commands

```bash
poetry run pytest -q
python scripts/sync_free_modules_registry.py
make stabilize-fast <category>
make stabilize-shared <category>
make stabilize-release <category>
make community-dist-install
```

Use a temporary mirror only when your network requires it:

```bash
RAPIDKIT_PYPI_MIRROR=<https-url> make community-dist-install
```

Do not commit local mirror or proxy values.

## Module Development

Start with:

- `dev-engine/playbooks/modules/MODULE_QUICK_REFERENCE.md`
- `dev-engine/playbooks/modules/MODULE_DEVELOPMENT_PROMPT.md`
- `dev-engine/playbooks/modules/MODULE_STABILIZATION_PROMPT.md`

Minimum module expectations:

- stable `module.yaml`
- generated code imports cleanly
- docs and changelog are useful
- tests cover generated behavior
- supported kits pass stabilization

## Release Confidence

Before release:

```bash
make stabilize-release-all
make community-dist-install
./dev-engine/validate_ai_security.sh
```

Attach or preserve the relevant output under `dev-engine/audit-history/`.

## Related Docs

- [Module Overview](../modules/overview.md)
- [Module Validation](module-validation.md)
- [Override Contracts](override-contracts.md)
- [Testing](../testing/README.md)
- [GitHub Actions Overview](github-actions-overview.md)
