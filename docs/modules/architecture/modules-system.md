# RapidKit Modular System

Last updated: 2026-06-04

The modular system packages framework-ready backend capabilities and installs them into generated
workspaces through the RapidKit core CLI.

## Architecture

- **Module source**: `src/modules/free/<category>/<slug>/`
- **Manifest**: `module.yaml`
- **Registry**: `src/modules/free/modules.yaml`
- **Kits**: `src/kits/**`
- **Audit evidence**: `dev-engine/audit-history/`
- **Operator playbooks**: `dev-engine/playbooks/`

The manifest owns dependencies, generated outputs, configuration, docs, and runtime support. The
registry is derived/curated listing metadata.

## Installation Lifecycle

1. The CLI loads the target project metadata.
1. It resolves module dependencies through `module.yaml`.
1. It renders base, variant, vendor, and snippet templates.
1. It writes generated files into the project.
1. It records module state and hashes under `.rapidkit`.
1. It surfaces conflicts instead of silently overwriting user edits.

## Snippet Lifecycle

Snippets are declared in `config/snippets.yaml` and rendered from `templates/snippets/`. Runtime
verification should be part of release gates for snippet-owning modules.

Important commands:

```bash
rapidkit reconcile --plan
rapidkit reconcile
make snippet-runtime-gate
```

## Stabilization Lifecycle

Use three levels of confidence:

```bash
make stabilize-fast <category>      # cached isolated kit installs
make stabilize-shared <category>    # one shared integration project per kit
make stabilize-release <category>   # both gates
```

Full catalog:

```bash
make stabilize-release-all
```

## Registry Hygiene

After module changes:

```bash
python scripts/sync_free_modules_registry.py
poetry run pytest -q tests/modules/test_module_consistency.py
```

Do not manually claim kit compatibility unless the corresponding stabilization evidence exists.

## Adding a Module

1. Confirm an existing module cannot be improved instead.
1. Add module directory and manifest.
1. Add templates and snippets.
1. Add docs and changelog.
1. Add tests.
1. Sync registry.
1. Run release gates.
1. Store evidence under `dev-engine/audit-history/`.

## Public Distribution

The community distribution is built from mapping files and finalized by
`scripts/finalize_distribution.py`. Validate it with:

```bash
make community-dist-install
```

Package mirrors and proxies are runtime escape hatches only. They must not be hard-coded into public
module metadata.
