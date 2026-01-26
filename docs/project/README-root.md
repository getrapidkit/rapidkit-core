# RapidKit — repository overview

RapidKit — repository overview

Short summary

RapidKit is a multi-purpose toolkit for generating and managing microservice/app starter projects
(Python backends, frontend templates, and deployment tooling). This file is a compact entry-point
for contributors to quickly find important folders, common developer commands, and repository
hygiene notes.

Quick checklist (what to do first)

- Ensure you have Python 3.10.14 installed (project uses a workspace `.venv`).
- Install or allow `direnv` (recommended) to auto-activate the workspace venv.
- Read `docs/getting-started/README.dev.md` for onboarding details and dev workflows.

Repository layout (top-level, short purpose)

- `src/` — core library and CLI implementation.
- `modules/` — kit/module templates and module manifests.
- `boilerplates/` — project templates and example apps.
- `dev/` — developer docs, cheat-sheets, and local guides.
- `licenses/` — security/policy docs, signing policy, and related notes.
- `docs/` — generated or authorative documentation.
- `tests/` — pytest tests and fixtures.
- `dist/` — build artifacts (ignored).
- `.venv/`, `.direnv/`, `.rapidkit/` — local runtime and cache directories (ignored).

Quick dev bootstrap

Make a project venv and install dependencies (one-off):

```bash
# Install dependencies and create venv
poetry install

# Optional: open a Poetry shell
poetry shell

# Run tests
poetry run pytest

# CLI help
poetry run rapidkit --help
```

Repository layout (short)

- `src/` — core library and CLI
- `src/modules/` — kit/module templates and module manifests
- `boilerplates/` — example app templates
- `docs/` — project documentation
- `tests/` — pytest tests and fixtures

Where to look next

- Developer onboarding: `getting-started/README.dev.md`
- Contribution guide: `contributing/CONTRIBUTING.md`
- Advanced topics: `advanced/architecture.md`, `advanced/lifecycle.md`

______________________________________________________________________

If you'd like, I can further expand this file with quick badges and links to CI artifacts.

- If you find a large file accidentally committed (for example environment artifacts), prefer
  `git rm --cached <file>` and commit the removal so the file remains on disk but is no longer
  tracked.
