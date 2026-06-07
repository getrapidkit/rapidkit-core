# RapidKit Core Documentation Hub

Last updated: 2026-06-04

This documentation covers the RapidKit core engine: the Python package that ships the module
catalog, framework kits, distribution tooling, and the `rapidkit` / `rkc` command surface used by
the npm wrapper and Workspai.

## Current Platform Snapshot

- Public package: `rapidkit-core`
- Python CLI entry points: `rapidkit`, `rkc`
- npm wrapper: `rapidkit`
- Free module catalog: 52 stable modules under `src/modules/free`
- Supported release kits: `fastapi.standard`, `fastapi.ddd`, `nestjs.standard`
- Canonical audit evidence: `dev-engine/audit-history/`
- Operator playbooks: `dev-engine/playbooks/`

## Documentation Map

| Section                                                | Purpose                                                             |
| ------------------------------------------------------ | ------------------------------------------------------------------- |
| [Getting Started](getting-started/README.md)           | Install and use RapidKit Core directly.                             |
| [Developer Guide](developer-guide/README.md)           | Contribute to the engine, modules, and kits.                        |
| [Modules](modules/overview.md)                         | Understand module manifests, registry, snippets, and stabilization. |
| [API Reference](api-reference/README.md)               | CLI command reference and machine-readable surfaces.                |
| [Configuration](configuration/CONFIG_FILES.md)         | Config files used by generated projects and the engine.             |
| [Deployment](deployment/PACKAGE_DISTRIBUTION_GUIDE.md) | Build, verify, and publish the community distribution.              |
| [Testing](testing/README.md)                           | Test strategy, coverage, and release gates.                         |
| [Contributing](contributing/CONTRIBUTING.md)           | Contribution flow and PR expectations.                              |
| [Licensing](licensing/OVERVIEW.md)                     | Licensing boundaries for the public package and generated assets.   |
| [Internal Docs](internal/)                             | Maintainer-only release, mapping, and policy references.            |

## Recommended Entry Points

For public users:

1. Install the npm CLI: `npm install -g rapidkit`
1. Use Workspai for a graphical workflow when needed.
1. Use the Python package directly only when building or debugging the core.

For maintainers:

1. Read `dev-engine/README.md`.
1. Use `dev-engine/playbooks/modules/MODULE_QUICK_REFERENCE.md`.
1. Run `make stabilize-release <category>` for module release confidence.
1. Run `make community-dist-install` before publishing.

## Release Evidence Rule

New stabilization, security, distribution, and shared-integration artifacts must be written under:

```text
dev-engine/audit-history/
```

Legacy docs may remain under `dev-engine/audit-history/legacy/`, but new docs should not reference
retired sandbox paths as active workflow locations.
