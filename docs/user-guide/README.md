# 📖 RapidKit User Guide

The RapidKit Community edition helps you scaffold production-ready backend services with a single
standard kit per supported framework (FastAPI today). This guide walks through day-to-day usage once
you have the CLI installed.

______________________________________________________________________

## 🚀 Getting Started

### Install the CLI

```bash
# Recommended: isolated install via pipx
pipx install rapidkit-core

# Alternative: install into the active interpreter
pip install rapidkit-core

rapidkit --version
```

### Scaffold Your First Project

```bash
rapidkit create project fastapi.standard MyService
cd MyService

# Bootstrap the project and install dependencies
rapidkit init

# Launch the development server
rapidkit dev
```

The interactive wizard (`rapidkit create`) lists every kit available in the current distribution.
For FastAPI, the generated project ships with a clean architecture layout, Docker assets, testing
setup, and module hooks.

______________________________________________________________________

## 🧩 Manage Modules

Modules extend generated projects without hand-editing boilerplate. Explore the catalog and install
components as needed:

```bash
rapidkit modules list                # Show available modules grouped by tier
rapidkit add module logging          # Enable structured logging
rapidkit add module security         # Add JWT authentication scaffolding
rapidkit add module database.postgres # Switch the database profile
```

Common community modules include:

| Module                  | Purpose                                                        |
| ----------------------- | -------------------------------------------------------------- |
| `settings`              | Environment-aware configuration system (installed by default)  |
| `logging`               | Structured logging with JSON/console output profiles           |
| `security`              | Authentication & authorization helpers (JWT, password hashing) |
| `database.postgres`     | Production-ready Postgres configuration                        |
| `observability.metrics` | Metrics exporter hooks                                         |

Use `rapidkit modules info <module>` for detailed metadata, dependencies, and compatibility.

### Keep the Modules Lock Updated

Generated projects maintain `.rapidkit/modules.lock.yaml` for reproducible installs. After adding or
updating modules in the distribution, rebuild the lock:

```bash
rapidkit modules lock --overwrite
rapidkit modules lock --check   # CI-friendly validation
```

Commit lock changes together with module updates.

______________________________________________________________________

## 🧭 Project Commands

Inside a generated project, the CLI detects `.rapidkit/project.json` and relays commands through
Poetry so the correct virtual environment is used.

```bash
rapidkit init     # Bootstrap a generated project (create local launcher + install deps)
rapidkit dev      # Start the development server
rapidkit test     # Run the bundled test suite
rapidkit lint     # Execute linting checks (Ruff + MyPy)
rapidkit format   # Auto-format with Ruff
rapidkit build    # Build production assets
```

### Bootstrapping explained

Run `rapidkit init` to prepare a newly generated project for development. The command is
project-aware and will:

- For FastAPI (Python) projects: create a local `.venv` if missing, ensure `poetry` is available and
  run `poetry install`.
- For Node (NestJS) projects: delegate to the project's local launcher if present, or use
  pnpm/yarn/npm to install node dependencies.

This makes `rapidkit init` the recommended first step for new users.

The generated Makefile wraps these commands:

```bash
make test
make lint
make format
make dev
```

Use whichever interface fits your workflow.

______________________________________________________________________

## 🐳 Docker & Deployment

Every project includes container assets in the `docker/` directory.

```bash
# Local development stack
docker compose up --build

# Run in the background
docker compose up -d

# View logs
docker compose logs -f

# Teardown
docker compose down
```

For production, combine `docker-compose.yml` with the provided overrides or integrate the generated
Dockerfile into your orchestration platform.

______________________________________________________________________

## 🔁 Upgrades & Template Diffing

Keep generated projects aligned with upstream templates:

```bash
rapidkit upgrade              # Pull latest distribution templates
rapidkit diff                 # Preview template changes against your project
rapidkit merge                # Apply compatible updates automatically
rapidkit checkpoint create    # Snapshot before applying breaking changes
rapidkit rollback <checkpoint> # Revert to a stored snapshot
```

Review diffs in Git before committing merged changes.

______________________________________________________________________

## 🧪 Quality & Testing

RapidKit projects ship with pytest, Ruff, and MyPy configured out of the box.

```bash
poetry run pytest
poetry run pytest --cov=src --cov-report=term-missing
poetry run ruff check src tests
poetry run mypy src
```

Launch the full pre-commit suite when contributing back to the distribution:

```bash
poetry run pre-commit run --all-files
```

______________________________________________________________________

## 🛠️ Troubleshooting

| Issue                           | Resolution                                                                                                        |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `rapidkit` command not found    | Ensure `pipx ensurepath` (or your Python scripts directory) is on `PATH`.                                         |
| Poetry not installed            | Install Poetry with `curl -sSL https://install.python-poetry.org \| python3 -`, then restart your shell.          |
| Module install fails            | Run `rapidkit modules validate` to confirm manifests are healthy.                                                 |
| Lock file drift detected        | Re-run `rapidkit modules lock --overwrite` and commit the result.                                                 |
| Missing dependencies at runtime | Run `rapidkit init` to re-bootstrap the project (or run `poetry install` manually inside the project virtualenv). |

Need more help? Open a discussion or issue on GitHub and include the RapidKit version plus the
command you attempted.

______________________________________________________________________

## 📚 Related Documentation

- [docs/getting-started/README.md](../getting-started/README.md)
- [docs/modules/overview.md](../modules/overview.md)
- [docs/developer-guide/README.md](../developer-guide/README.md)
- [docs/licensing/OVERVIEW.md](../licensing/OVERVIEW.md)

Happy shipping! RapidKit’s community edition is designed to stay predictable while you iterate.
