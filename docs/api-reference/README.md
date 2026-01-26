# 📚 RapidKit CLI & API Reference

This reference captures the community-facing surface area of RapidKit. It focuses on:

- Commands provided by the `rapidkit` CLI shipped in the community distribution
- How to manage modules, locks, and project upgrades safely
- Programmatic entry points that are considered stable enough for automation

> ℹ️ Everything documented here is available in the open-source repository. Commercial-only
> extensions and internal tooling live outside this guide.

______________________________________________________________________

## 🚀 CLI Overview

`rapidkit` ships as a Typer application with a single entry point and multiple command groups. Use
`rapidkit --help` at any time to view the latest options.

### Global Commands (run anywhere)

| Command                      | Purpose                                                               |
| ---------------------------- | --------------------------------------------------------------------- |
| `rapidkit create`            | Scaffold a new project from an available kit (interactive by default) |
| `rapidkit add module <name>` | Install a module into the current project using the module registry   |
| `rapidkit list`              | Display the kits that ship with the current distribution              |
| `rapidkit info`              | Show version information and kit metadata                             |
| `rapidkit frameworks`        | List available framework adapters and their standard kits             |
| `rapidkit upgrade`           | Pull the latest template updates from this distribution               |
| `rapidkit diff`              | Compare your project against the latest kit templates                 |
| `rapidkit merge`             | Apply non-breaking template changes into an existing project          |
| `rapidkit rollback`          | Roll back template updates using checkpoints                          |
| `rapidkit checkpoint`        | Snapshot project files for later restore                              |
| `rapidkit optimize`          | Run project cleanups such as pruning temp files                       |
| `rapidkit snapshot`          | Capture template state for auditing                                   |
| `rapidkit doctor`            | Diagnose local environment issues before scaffolding                  |
| `rapidkit license`           | Inspect and activate module or kit licenses                           |
| `rapidkit modules`           | Explore module utilities (see below)                                  |
| `rapidkit --tui`             | Launch the interactive wizard when the TUI is installed               |

### Project Commands (run inside a RapidKit project)

These commands auto-detect the local project using `.rapidkit/project.json` and delegate through
Poetry so the correct virtual environment is used.

| Command           | Purpose                                                                 |
| ----------------- | ----------------------------------------------------------------------- |
| `rapidkit init`   | 🔧 Bootstrap the project (create local launcher & install dependencies) |
| `rapidkit dev`    | Start the development server defined by the selected kit                |
| `rapidkit start`  | Boot the production server profile                                      |
| `rapidkit build`  | Build production assets                                                 |
| `rapidkit test`   | Run the project's test suite                                            |
| `rapidkit lint`   | Execute linting checks (Ruff, MyPy, etc.)                               |
| `rapidkit format` | Format code according to project standards                              |
| `rapidkit help`   | Display project-level help from the generated CLI                       |

```bash
# Example workflow
rapidkit create project fastapi.standard my-api
cd my-api
# bootstrap project and install runtime deps
rapidkit init
rapidkit add module logging
rapidkit dev
```

______________________________________________________________________

## 🧩 Modules Toolkit

`rapidkit modules` exposes a rich set of utilities for authoring, validating, and maintaining
modules. Run `rapidkit modules --help` to see the full tree. Frequently used commands include:

```bash
rapidkit modules list                     # Show modules by tier/profile
rapidkit modules info logging             # Inspect manifest metadata
rapidkit modules status                   # Report tracked files inside a project
rapidkit modules lock --overwrite         # Regenerate .rapidkit/modules.lock.yaml
rapidkit modules validate                 # Validate module manifests and structure specs
rapidkit modules scaffold my_module       # Create a new module skeleton (prompts for metadata)
rapidkit modules compare logging          # Compare installed files with template snapshots
rapidkit modules sign path/to/module.yaml # Verify manifest signatures
```

Key behaviours:

- **Lock rebuilds**: `modules lock --overwrite` reads every module manifest and writes a
  deterministic lock file used by generated projects.
- **Validation**: `modules validate` ensures manifests follow the settings module contract,
  including schema files, overrides, and hook definitions.
- **Scaffolding**: `modules scaffold` generates a minimal module layout using current best
  practices, including `module.yaml`, configuration stubs, and test placeholders.

______________________________________________________________________

## 🔐 License Management

The community edition includes license tooling so future marketplace modules follow the same flow.

```bash
rapidkit license status                # List activated kit or module licenses
rapidkit license activate licenses/kits/fastapi.standard.json
rapidkit license inspect <license-id>  # Inspect license metadata
```

Community kits ship with permissive licenses (MIT or Apache-2.0). The CLI validates signatures and
expiry dates before enabling any gated modules.

______________________________________________________________________

## 📦 Kits & Frameworks

- `rapidkit list` shows the kits shipped with the current build. Every supported framework provides
  a single **standard** kit.
- `rapidkit frameworks` mirrors that information grouped by framework family (e.g. FastAPI, NestJS
  when available).
- Kits are described by `kit.yaml` files inside `src/kits/<family>/<variant>/`.

When authoring new kits, update the registry and ensure `docs/modules/overview.md` and relevant
guide sections reflect the new structure before shipping.

______________________________________________________________________

## 🗃️ Modules Lock File

RapidKit projects maintain `.rapidkit/modules.lock.yaml` to guarantee reproducible installs.

```bash
rapidkit modules lock --overwrite      # Rebuild lock from manifests
rapidkit modules lock --check         # Verify the lock is up to date (CI friendly)
rapidkit modules status --json        # Inspect lock usage per file
```

Lock files record module versions, checksums, and profiles so upgrades remain predictable. Commit
changes whenever new modules or versions are added to the distribution.

______________________________________________________________________

## 🧰 Python Entry Points

While the CLI covers most workflows, a handful of modules are stable enough for automation. Import
from the installed `rapidkit` package:

```python
from rapidkit.cli.main import main as rapidkit_main
from rapidkit.modules.registry import get_all_modules
from rapidkit.modules.lock import build_lock, write_lock
from rapidkit.core.services.project_creator import ProjectCreatorService
```

Guidelines:

- Keep imports within the `cli`, `core`, `kits`, and `modules` packages. The `experimental` package
  is not part of the compatibility contract.
- Prefer CLI commands in scripts when possible—Python APIs may surface additional exceptions.
- Pin the RapidKit version in automation to avoid breaking changes across major releases.

______________________________________________________________________

## ⚙️ Automation Patterns

- **Upgrade safety**: Combine `rapidkit diff` and `rapidkit merge` in CI to preview and apply safe
  template updates before rolling them into downstream projects.
- **Quality gates**: Use generated Make targets (`make test`, `make lint`, `make dev`) or invoke
  `rapidkit test` / `rapidkit lint` directly for consistent tooling across teams.
- **Distribution builds**: The publishing workflow runs `make community-docs` so README artifacts
  are always up to date. Run it locally before cutting a release to catch forbidden keywords or
  missing docs.

______________________________________________________________________

## 🙋 Need More Help?

- `rapidkit --help` and `rapidkit <command> --help` for inline guidance
- [docs/getting-started/](../getting-started/README.md) for onboarding
- [docs/modules/overview.md](../modules/overview.md) for module authoring conventions
- [docs/developer-guide/](../developer-guide/README.md) for contribution standards

Happy building! The more automation and modules you ship, the better RapidKit becomes for the entire
community.
