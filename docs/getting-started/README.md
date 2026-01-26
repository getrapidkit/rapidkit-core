# 🚀 RapidKit – Getting Started

Welcome! This guide helps you install RapidKit, scaffold your first project, and explore the module
ecosystem. Everything here applies to the single RapidKit Community edition.

## 📋 Requirements

- Python 3.10+
- Git (for cloning repositories or managing generated projects)

## 🎯 Install the CLI

RapidKit is published to PyPI. Install it into a virtual environment or your preferred toolchain.

```bash
pip install rapidkit

# Verify install
rapidkit --version
```

> Prefer a local checkout? Clone `https://github.com/getrapidkit/core` and run `poetry install` from
> the repository root.

## 🛠️ Create Your First Project

```bash
# Launch the interactive wizard (recommended)
rapidkit create

# Prefer non-interactive scaffolding?
rapidkit create project fastapi.standard MyProject

cd MyProject

# Bootstrap the generated project and install dependencies (recommended)
# This creates the local project launcher and a reproducible environment
rapidkit init

# Run the development server via the project-aware CLI
rapidkit dev
```

## Bootstrapping explained

Use `rapidkit init` as the recommended, project-aware bootstrap step after generating a project. It
automates the common first-run tasks so new users don't need to remember multiple commands.

- Python / FastAPI projects: `rapidkit init` will create a `.venv` (if missing), ensure `poetry` is
  available, and run `poetry install` inside the project virtual environment.
- Node / NestJS projects: `rapidkit init` prefers the project's local launcher
  (`.rapidkit/rapidkit`) when present or falls back to a node package manager (pnpm/yarn/npm) to run
  the install.

This makes `rapidkit init` the simplest, least error-prone way to prepare a generated project for
development. Advanced users can still run `poetry install` / `pip install -r requirements.txt` or
native node package manager commands themselves.

RapidKit projects rely on Poetry for dependency management. A `requirements.txt` file is not
generated; export one with `poetry export --format requirements.txt --output requirements.txt` if a
tool requires it.

### Prefer the interactive TUI?

```bash
rapidkit --tui
```

The TUI walks through kit selection, module choices, and post-generation tasks.

## 📁 Generated Project Overview

```text
MyProject/
├── src/
│   ├── main.py              # FastAPI entrypoint
│   ├── core/                # Shared services and settings
│   └── modules/             # Optional modules wired into the kit
├── tests/                   # Unit and integration tests
├── pyproject.toml           # Poetry configuration
├── README.md                # Project overview
└── docker/                  # Dockerfile + compose helpers
```

Key characteristics:

- Clean Architecture layout with domain/application separation
- Environment-aware settings powered by Pydantic
- Ready-to-run Docker assets (`docker-compose.yml` + overrides)
- Quality gates preconfigured (pytest, Ruff, MyPy, coverage)

## 🧩 Add Modules

RapidKit ships a catalog of community modules. Install them right after project scaffolding:

```bash
# Add authentication scaffolding
rapidkit add module auth

# Swap SQLite for PostgreSQL
rapidkit add module database

# Enable structured logging
rapidkit add module logging
```

Marketplace modules follow the same structure used by the community settings module: declarative
configuration, schema validation, and idempotent installers. License tools
(`rapidkit license status`, `rapidkit license activate`) are built into the CLI so premium modules
follow the identical workflow when they ship.

## 🐳 Docker & Local Ops

Generated projects include Docker support by default:

```bash
# Build and run the stack
docker compose up --build

# Run in the background
docker compose up -d

# Tail logs
docker compose logs -f

# Tear down services
docker compose down
```

For development overrides, use the provided `docker-compose.dev.yml` file or extend the
configuration under `docker/`.

## 🔁 Day-to-day Commands

```bash
# Tests & coverage
poetry run pytest
poetry run pytest --cov=src

# Formatting & linting
poetry run ruff check src
poetry run ruff format src

# Type checking
poetry run mypy src
```

Make targets in the generated project (`make test`, `make lint`, `make dev`) wrap these commands if
you prefer a Makefile-driven workflow.

## 📚 Continue Exploring

- **Module System** – `../modules/overview.md`
- **Developer Guide** – `../developer-guide/README.md`
- **CLI Reference** – `../api-reference/README.md`
- **Configuration Deep Dive** – `../configuration/CONFIG_FILES.md`
- **Testing Practices** – `../testing/README.md`

## 🤝 Need Help?

- Join the conversation in [GitHub Discussions](https://github.com/getrapidkit/core/discussions)
- Report bugs or request features via [GitHub Issues](https://github.com/getrapidkit/core/issues)
- Improve the docs by opening a pull request in this repository

______________________________________________________________________

**You're ready to build with RapidKit.** Scaffold a project, wire in modules, and share your
feedback with the community!
