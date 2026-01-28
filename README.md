# RapidKit Core (Pre-release / RC)

This is the **pre-release channel** for RapidKit Core.

- Website: https://www.getrapidkit.com/
- Docs: https://www.getrapidkit.com/docs
- Staging repo: https://github.com/getrapidkit/community-staging
- Stable repo: https://github.com/getrapidkit/community

## What you get

- A production-grade scaffolding engine for FastAPI + NestJS
- A consistent modules system (install, uninstall, upgrade, diff)
- Project-aware commands (`init`, `dev`, `build`, `test`, `lint`, `format`)
- Docker-ready defaults and quality gates

## Install

The PyPI project is `rapidkit-core` and the CLI command is `rapidkit`.

```bash
# Recommended: isolated CLI (supports prereleases)
pipx install --pip-args="--pre" rapidkit-core

# Or: in the current interpreter
python -m pip install --pre -U rapidkit-core

rapidkit --version
rapidkit --help
```

## Quick start

```bash
# Create a project (interactive)
rapidkit create

# Or: non-interactive
rapidkit create project fastapi.standard my-api

cd my-api
rapidkit init
rapidkit dev
```

## Notes (important)

- RC builds can include breaking changes between versions.
- There is also an npm package named `rapidkit` that provides a `rapidkit` command. If you install
  both globally, whichever one comes first in your PATH will run.
