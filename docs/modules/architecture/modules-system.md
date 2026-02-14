# RapidKit Modular System

The RapidKit modular system packages framework-ready capabilities that can be injected into any
generated project. This document explains how modules are organised, how the CLI provisions them,
and which quality gates keep the catalog production ready.

## High-level architecture

- **Repository layout** – Modules live under `src/modules/<tier>/<category>/<module>/`. The free
  distribution ships categories such as `core`, `auth`, `cache`, `database`, `observability`,
  `security`, `tasks`, and `communication`.
- **Catalog index** – `src/modules/<tier>/modules.yaml` is the tier-level catalog for availability,
  human metadata, and kit support. It powers listings/search and can gate installation (e.g.
  planned/active).
- **Module manifest** – Each module’s `module.yaml` is the canonical source of truth for the
  dependency graph (`depends_on`) and generation outputs (variants/vendor/files).
- **Structure spec** – `src/modules/STRUCTURE.yaml` (spec v3) defines the mandatory directory tree,
  required files, and flexible subtrees. Validators enforce the spec locally and in CI.
- **Generators** – Each module exposes a `generate.py` that extends
  `modules.shared.generator.module_generator.BaseModuleGenerator` and delegates to framework plugins
  in `frameworks/`.
- **Framework plugins** – FastAPI and NestJS plugins expose template mappings, output paths, and
  pre/post hooks. They guarantee parity across frameworks.
- **Snippet registry** – `config/snippets.yaml` registers reusable fragments consumed by the global
  `SnippetRegistry`, enabling composable inserts without duplicating template content. The project
  tracks applied/pending injections in `.rapidkit/snippet_registry.json` and can converge state via
  `rapidkit reconcile`.
- **Vendor payloads** – Templates under `templates/vendor/` render into
  `.rapidkit/vendor/<module>/<version>` so upgrades remain reproducible.
- **State tracking** – `.module_state.json` stores file hashes during generation so the CLI can
  detect local modifications before applying updates.

## CLI surface

All module commands are exposed via `rapidkit modules ...`:

| Command                                                           | Purpose                                                      |
| ----------------------------------------------------------------- | ------------------------------------------------------------ |
| `rapidkit modules list`                                           | Summarise available modules, tags, and current versions      |
| `rapidkit modules info free/essentials/settings`                  | Show registry metadata for a single module                   |
| `rapidkit modules scaffold my_module --tier free --category core` | Create a spec-compliant scaffold using maintained blueprints |
| `rapidkit modules validate-structure free/essentials/settings`    | Validate directory layout against `STRUCTURE.yaml`           |
| `rapidkit modules vet free/essentials/settings`                   | Run structure + parity checks, updating `module.verify.json` |
| `rapidkit modules snapshot free/essentials/settings`              | Emit a signed hash snapshot for release pipelines            |
| `rapidkit modules lock --overwrite`                               | Regenerate `.rapidkit/modules.lock.yaml` in a project        |
| `rapidkit modules outdated`                                       | Compare lock state vs registry versions                      |
| `rapidkit modules search logging`                                 | Search for modules by name, description, or tags             |

Additional helpers include `rapidkit modules configure` (record module defaults per project),
`rapidkit modules migration-template` (generate markdown stubs), and
`rapidkit modules summary --json` (machine-readable inventory export).

## Snippet injection lifecycle

Snippet injection is a first-class part of module installation and upgrades. RapidKit records
snippet state transitions in `.rapidkit/snippet_registry.json`, supports diff-only planning via
`rapidkit reconcile --plan`, and provides rollback/conflict workflows.

See [docs/modules/architecture/snippet-architecture.md](snippet-architecture.md) for the complete
architecture, states, safety rules, and CLI commands.

## Installation workflow

1. `rapidkit add module <name>` consults the tier catalog (`src/modules/<tier>/modules.yaml`) for
   availability and high-level metadata, then loads the module manifest (`module.yaml`) to resolve
   dependencies (`depends_on`) and generation recipes.
1. The CLI renders vendor assets into a temporary directory using the module generator and framework
   plugins.
1. Snippets are injected into target files based on anchors and enabled features.
1. Generated files are copied into the project, existing files are diffed, and conflicts are
   surfaced interactively.
1. Hashes are recorded in `.rapidkit/modules.lock.yaml` and `.rapidkit/modules.hashes.json` so
   future updates detect drift.
1. Vendor payloads are stored under `.rapidkit/vendor/<module>/<version>` for rollback and
   idempotent replays.
1. Generated project files are written under `src/modules/<tier>/<category>/<module>/...` inside the
   target project, mirroring the module slug. Use `scripts/migrate_modules_to_src_modules.py` to
   rewrite legacy manifests that still point at `src/<category>/...`.

## Quality gates

- **Structure validation** – `python scripts/validate_module_structure.py --paths ...` and
  `rapidkit modules validate-structure` must pass for every module.
- **Parity validation** – `python scripts/audit_module_parity.py --module <slug> --json` ensures
  FastAPI and NestJS outputs remain aligned (routes, health endpoints, dependency wiring).
- **Coverage** – Module-specific pytest suites under `tests/modules/**` must maintain ≥85% coverage;
  failing modules block releases.
- **Manifest hygiene** – `rapidkit modules vet` updates `module.verify.json` so downstream tooling
  can trust module fingerprints.
- **Lock discipline** – `rapidkit modules lock` is run after every release to synchronise
  `.rapidkit/modules.lock.yaml` with the registry.

## Working with the registry

The tier catalog (`src/modules/<tier>/modules.yaml`) is intentionally redundant: it centralises
listing metadata (status/version/docs/kit support) and installer gating. The module manifest
(`module.yaml`) remains the canonical dependency and generation contract.

When bumping a module version:

1. Update the module directory (templates, docs, tests, metadata).
1. Regenerate `module.verify.json` by running `rapidkit modules vet <slug>`.
1. Update the corresponding entry in `src/modules/<tier>/modules.yaml` (version/status/docs/kit
   support).
1. Run `rapidkit modules summary --json` to confirm the registry entry resolves correctly.
1. Commit the module changes and the registry update together.

## Distribution bundles

Community distributions bundle a subset of scripts, docs, and templates declared in engine-source
mapping files such as `scripts/scripts_map.yml` and `docs/docs_map.yml`. Those map files are
maintainer assets and may not be present in every published mirror repository. Because modules
reference vendor payloads and verification manifests directly, keeping the source tree accurate
guarantees downstream bundles inherit the right behaviour without patching generated artefacts.

## Recommended workflow for new modules

1. Scaffold with `rapidkit modules scaffold` and choose the appropriate blueprint.
1. Implement `generate.py` context hooks (`build_base_context`, `apply_variant_context_pre/post`,
   `post_variant_generation`).
1. Build FastAPI and NestJS plugins that surface identical services/routes.
1. Add base templates, snippet registrations, variant adapters, vendor payloads, and integration
   tests.
1. Flesh out docs (`README.md` plus the `docs/*` set) and ensure examples reference generated files.
1. Write pytest suites covering generator orchestration, runtime behaviour, overrides, vendor
   assets, and parity.
1. Run validators (`modules vet`, `audit_module_parity.py`, `pytest`) and refresh
   `module.verify.json`.
1. Update `modules.yaml`, bump the module version, and rebuild the lock file.

Following this workflow keeps the module catalog aligned with the RapidKit engine and prevents
regressions in downstream bundles.
