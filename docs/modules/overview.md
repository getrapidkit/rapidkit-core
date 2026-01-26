# RapidKit Module Overview

RapidKit modules extend generated projects with reusable capabilities. The repository ships a
curated free catalog under `src/modules/free`, and every module follows the spec v3 blueprint
declared in `src/modules/STRUCTURE.yaml`.

## Where modules live

- Module directories follow `src/modules/<tier>/<category>/<module>/`.
- `src/modules/<tier>/modules.yaml` is the tier-level catalog for availability and listing metadata
  (status/version/docs/kit support).
- Each module directory contains generator code, templates, docs, tests, and the manifest that
  powers dependency resolution and generation (`module.yaml`).

## Install modules into a project

```bash
# Inside a generated RapidKit project
rapidkit add module logging
rapidkit add module database
rapidkit add module settings --plan   # dry-run preview
```

The CLI resolves dependencies, renders templates into your project, records hashes inside
`.rapidkit/modules.lock.yaml`, and persists vendor snapshots for deterministic upgrades. All
generated files now land under `src/modules/<tier>/<category>/<module>/...` inside the target
project, mirroring the slug declared in `module.yaml`. Use
`scripts/migrate_modules_to_src_modules.py` to rewrite legacy manifests to this layout.

## Reference layout

```text
src/modules/free/essentials/settings/
├── .module_state.json
├── README.md
├── module.yaml
├── module.verify.json
├── config/
│   ├── base.yaml
│   └── snippets.yaml
├── docs/
│   ├── overview.md
│   ├── usage.md
│   ├── advanced.md
│   ├── migration.md
│   └── troubleshooting.md
├── frameworks/
│   ├── __init__.py
│   ├── fastapi.py
│   └── nestjs.py
├── generate.py
├── overrides.py
├── templates/
│   ├── base/
│   │   ├── settings.py.j2
│   │   ├── settings_health.py.j2
│   │   └── settings_types.py.j2
│   ├── snippets/
│   │   └── env.snippet.j2
│   ├── variants/
│   │   ├── fastapi/
│   │   │   ├── settings.py.j2
│   │   │   ├── settings_routes.py.j2
│   │   │   └── settings_health.py.j2
│   │   └── nestjs/
│   │       ├── settings.service.ts.j2
│   │       ├── settings.controller.ts.j2
│   │       └── settings.module.ts.j2
│   └── vendor/
│       └── nestjs/
│           └── configuration.js.j2
└── tests/
    └── ...
```

### Key assets

- `module.yaml` describes metadata, generation recipes, dependencies, and vendor outputs.
- `.module_state.json` captures file hashes so upgrades can detect drift safely.
- `module.verify.json` is the structure fingerprint used by validators and parity tooling.
- `generate.py` orchestrates rendering through `BaseModuleGenerator` and the framework plugins.
- `overrides.py` provides hooks for preserving user edits across upgrades.
- `templates/**` contains the runtime, framework variants, vendor payloads, snippets, and tests.
- `docs/**` and `README.md` ship the module-specific documentation set required by spec v3.
- `tests/modules/...` (outside the module directory) provide regression coverage (≥85%).

## Quality gates

- Run `rapidkit modules validate-structure <slug>` to confirm the layout matches `STRUCTURE.yaml`.
- Run `rapidkit modules vet <slug>` to combine structure validation with FastAPI/NestJS parity
  checks.
- Execute `python scripts/audit_module_parity.py --module <slug>` for the detailed parity report
  used in CI.
- Maintain ≥85% pytest coverage across `tests/modules/**` and include integration smoke templates
  under `templates/tests/`.
- Keep module docs synchronized with code changes; parity tooling reads `module.verify.json` to
  ensure docs/tests exist.

## Helpful commands

```bash
rapidkit modules list                        # Discover available modules and metadata
rapidkit modules info free/essentials/settings     # Inspect registry entry and version
rapidkit modules snapshot free/essentials/settings # Generate module hash snapshot
rapidkit modules lock --overwrite            # Refresh .rapidkit/modules.lock.yaml in a project
```

## Next steps

- Deep dive into the architecture details in `docs/modules/architecture/README.md`.
- Review authoring workflows and validator usage in `docs/modules/architecture/modules-system.md`.
- Explore module API surfaces (generators, plugins, snippets) in `docs/modules/architecture/api.md`.

Use the free `core/settings`, `core/logging`, and `core/deployment` modules as templates when
developing new assets.
