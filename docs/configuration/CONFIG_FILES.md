# 📋 Configuration Reference

This guide describes the configuration files that ship with the RapidKit Community distribution and
how they interact when you build or package projects.

______________________________________________________________________

## Project-Level Configuration

### `pyproject.toml`

- Defines the Python package metadata for the community CLI (`rapidkit`)
- Declares runtime dependencies (`typer`, `jinja2`, `pydantic`, etc.) and dev tools (pytest, Ruff,
  MyPy, Black)
- Configures tooling sections such as `tool.mypy`, `tool.ruff`, and coverage defaults
- Registers the CLI entry point via `tool.poetry.scripts`

Common commands:

```bash
poetry show           # Inspect dependency graph
poetry add <package>  # Add a dependency to the distribution
poetry version patch  # Bump the package version before releasing
```

### `poetry.lock`

- Auto-generated lock file that pins exact dependency versions
- Keeps CI/CD environments reproducible
- Never edit manually—use `poetry lock`, `poetry update`, or `poetry add/remove`

### `pytest.ini`

- Configures pytest to search `tests/`
- Enables strict marker checks and coverage reporting against `src`
- Community workflows rely on the default options, so keep additions consistent with generated
  projects

```bash
poetry run pytest
poetry run pytest --cov=src --cov-report=term-missing
```

### `pyrightconfig.json`

- Provides strict settings for Pyright/Pylance in VS Code
- Mirrors the MyPy package roots (`src`) and excludes test fixtures
- Handy when contributors prefer static analysis directly in their editor

### `.pre-commit-config.yaml`

- Defines the linting and testing hooks executed by `poetry run pre-commit`
- Includes Ruff (lint & format), Black, MyPy, pytest, Bandit, and pip-audit
- Keep the hook list aligned with the Makefile so local and CI checks match

```bash
poetry run pre-commit install
poetry run pre-commit run --all-files
```

______________________________________________________________________

## Documentation & Distribution Files

Community distributions consume pre-rendered docs artifacts and workflow templates generated in the
engine source repository.

- Maintainer-only mapping files (for example `docs/docs_map.yml` and `scripts/scripts_map.yml`) are
  part of the engine build pipeline and may not be present in every published mirror.
- The docs utility `scripts/manage_community_docs.py` is an engine release helper used before
  distribution sync; it is not required for day-to-day usage of the published `rapidkit-core`
  repository.

If you maintain the engine source itself, run the docs guard there:

```bash
make community-docs
```

______________________________________________________________________

## Generated Project Assets

Scaffolded applications include their own configuration files (e.g., `pyproject.toml`, `docker`
folder, `.rapidkit/modules.lock.yaml`). Those files live inside each generated project and are
documented in [docs/user-guide/README.md](../user-guide/README.md) and
[docs/modules/overview.md](../modules/overview.md).

When updating template configuration, keep this distribution and the generated projects in sync to
ensure upgrades remain predictable.
