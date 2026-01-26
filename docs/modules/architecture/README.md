# RapidKit Free Module Suite

Authoritative guide for developing and validating free-tier RapidKit modules against the spec v3
blueprint. Each module must remain production-ready, framework-aligned, and consistent with the
scaffolding pipeline that powers the CLI (`rapidkit add module`).

## Spec v3 at a glance

- The canonical blueprint lives in `src/modules/STRUCTURE.yaml` (`spec_version: 3`).
- Every module directory is located at `src/modules/<tier>/<category>/<module>/`.
- Required assets include manifests, generator code, framework plugins, templates, docs, and tests.
- Structure verification fingerprints are stored in `module.verify.json` and enforced by validators.
- Tests must maintain ≥85% coverage across `tests/modules/**` with parity between FastAPI and NestJS
  variants.

## Directory blueprint

```text
<tier>/<category>/<module>/
├── .module_state.json            # Hash ledger maintained by the generator
├── README.md                     # Concise module landing page
├── module.yaml                   # Metadata, dependencies, generation recipes
├── module.verify.json            # Structure fingerprint consumed by validators
├── config/
│   ├── base.yaml                 # Default configuration exposed to templates
│   └── snippets.yaml             # Snippet registry entries
├── docs/
│   ├── README.md
│   ├── overview.md
│   ├── usage.md
│   ├── advanced.md
│   ├── migration.md
│   └── troubleshooting.md
├── frameworks/
│   ├── __init__.py
│   ├── fastapi.py                # FastAPI plugin registered with the generator
│   └── nestjs.py                 # NestJS plugin registered with the generator
├── generate.py                   # Entry point extending BaseModuleGenerator
├── overrides.py                  # Override preservation hooks
├── templates/
│   ├── base/                     # Framework-agnostic runtime assets
│   ├── variants/
│   │   ├── fastapi/              # FastAPI routes, adapters, health entrypoints
│   │   └── nestjs/               # NestJS services, controllers, modules
│   ├── snippets/                 # Injected fragments registered in config/snippets.yaml
│   ├── vendor/                   # Pre-rendered vendor payloads (.rapidkit/vendor/...)
│   └── tests/                    # Integration smoke templates rendered into projects
└── tests/                        # Pytest suite exercising generator + runtime behaviour
```

Use `src/modules/free/essentials/settings` as the reference implementation. It demonstrates the
required layout, framework parity, vendor assets, and documentation split.

## Key artefacts and expectations

- **`module.yaml`** – Defines module metadata, dependency graph, generation outputs, and vendor
  payloads.
- **`.module_state.json`** – Maintains hashes for generated files to detect drift during upgrades.
- **`module.verify.json`** – Captures structure metadata referenced by parity and structure
  validators.
- **`generate.py`** – Extends `modules.shared.generator.module_generator.BaseModuleGenerator` and
  wires framework plugins.
- **`frameworks/fastapi.py`, `frameworks/nestjs.py`** – Implement plugin contracts
  (`get_template_mappings`, `get_output_paths`, hooks).
- **`templates/base/*.j2`** – Shared runtime components consumed by every framework variant.
- **`templates/variants/<framework>/*.j2`** – Framework-specific adapters built on top of the shared
  runtime.
- **`templates/snippets/*.snippet.j2` + `config/snippets.yaml`** – Declarative snippet registrations
  consumed by `SnippetRegistry`.
- **`templates/tests/integration/*.j2`** – Integration test templates injected into generated
  projects.
- **`tests/modules/**`** – Real pytest suites targeting generator behaviour, runtime contracts,
  overrides, parity, and vendor assets.
- **`docs/**`** – Complete documentation set (overview, usage, advanced, migration, troubleshooting)
  required by spec v3.

## Generation pipeline

1. `rapidkit modules scaffold` creates the baseline directory tree and boilerplate files.
1. `generate.py` loads `module.yaml`, builds the base context, and orchestrates rendering through
   `BaseModuleGenerator`.
1. Framework plugins expose template mappings and output destinations for FastAPI and NestJS.
1. `TemplateRenderer` renders templates, falling back to a custom parser when Jinja2 is unavailable.
1. `SnippetRegistry` injects registered snippets based on target paths, features, and variants. See
   [docs/modules/architecture/snippet-architecture.md](snippet-architecture.md) for the full
   injection lifecycle (registry state, reconcile/plan, rollback, conflicts, patch modes).
1. Vendor payloads are written to `.rapidkit/vendor/<module>/<version>/` and copied into projects
   when required.
1. `.module_state.json` is updated with file hashes so subsequent upgrades can detect drift or
   conflicts.

## Validation layers

- `rapidkit modules validate-structure <slug>` – Enforces the spec v3 blueprint against
  `STRUCTURE.yaml`.
- `rapidkit modules vet <slug>` – Runs structure validation and FastAPI/NestJS parity checks,
  updating `module.verify.json`.
- `python scripts/validate_module_structure.py --paths src/modules/<tier>/<category>/<module>` –
  Batch validator used by pre-commit and CI.
- `python scripts/audit_module_parity.py --module <slug> --json` – Emits parity diagnostics for both
  frameworks.
- `pytest tests/modules/<tier>/<category>/<module> -q --cov=src/modules/<tier>/<category>/<module>`
  – Maintains ≥85% coverage.
- `rapidkit modules snapshot <slug>` – Produces a signed structure hash for release traceability.

## Documentation and testing obligations

- Keep README and docs in the module directory aligned with generated code; spec v3 requires the
  full set (overview, usage, advanced, migration, troubleshooting).
- Integration test templates under `templates/tests/integration/` must render working smoke tests in
  generated projects.
- Pytest suites should cover generator orchestration, override hooks, runtime behaviour, framework
  adapters, vendor payloads, and versioning.
- When introducing optional features, document configuration toggles and add coverage for
  enabled/disabled paths.

## Reference modules

- `free/essentials/settings` – Canonical blueprint for configuration-heavy modules.
- `free/essentials/logging` – Demonstrates cross-framework parity and snippet usage.
- `free/essentials/deployment` – Showcases vendor payloads, CI assets, and integration templates.

Review these modules before authoring new functionality to ensure parity with established patterns.
