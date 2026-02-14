# RapidKit Core

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)

RapidKit Core is the open-source RapidKit engine and CLI for scaffolding, operating, and evolving
production-ready backend projects.

- Package: `rapidkit-core`
- CLI: `rapidkit`
- Website: https://www.getrapidkit.com/
- Docs: https://www.getrapidkit.com/docs
- Repository: https://github.com/getrapidkit/rapidkit-core
- Issues: https://github.com/getrapidkit/rapidkit-core/issues
- Discussions: https://github.com/getrapidkit/rapidkit-core/discussions

## Useful tools

- RapidKit npm CLI: https://github.com/getrapidkit/rapidkit-npm
- npm package: https://www.npmjs.com/package/rapidkit
- RapidKit VS Code Extension: https://github.com/getrapidkit/rapidkit-vscode
- VS Code Marketplace: https://marketplace.visualstudio.com/items?itemName=rapidkit.rapidkit-vscode

## What you get

- Production-grade scaffolding for FastAPI and NestJS
- Consistent module lifecycle: add, remove, upgrade, diff, reconcile, rollback
- Project-aware commands for local development and CI workflows
- Standardized project structure with `.rapidkit/` metadata

## Install

```bash
# Recommended: isolated CLI
pipx install rapidkit-core

# Or: in the current interpreter
python -m pip install -U rapidkit-core

rapidkit --version
rapidkit --help
```

## Quick start

```bash
# Interactive wizard
rapidkit create

# Or: non-interactive
rapidkit create project fastapi.standard my-api

cd my-api
rapidkit init
rapidkit dev
```

## CLI surface

### Global commands

- `rapidkit version`, `rapidkit project`, `rapidkit list`, `rapidkit info`, `rapidkit commands`
- `rapidkit create`, `rapidkit add`, `rapidkit modules`, `rapidkit frameworks`
- `rapidkit upgrade`, `rapidkit diff`, `rapidkit merge`, `rapidkit optimize`
- `rapidkit doctor`, `rapidkit license`, `rapidkit checkpoint`, `rapidkit snapshot`
- `rapidkit reconcile`, `rapidkit rollback`, `rapidkit uninstall`
- `rapidkit --tui`, `rapidkit --version`, `rapidkit -v`

### Project commands

Inside a generated RapidKit project:

- `rapidkit init`
- `rapidkit dev`
- `rapidkit start`
- `rapidkit build`
- `rapidkit test`
- `rapidkit lint`
- `rapidkit format`
- `rapidkit help`

### Common examples

```bash
rapidkit create project
rapidkit create project fastapi.standard my-api
rapidkit create project nestjs.standard my-api
rapidkit create project fastapi.standard my-api --output /path/to/workspace

cd my-api && rapidkit init
rapidkit dev
rapidkit add module auth
rapidkit modules list
```

## Pre-releases (RC)

Pre-releases are published as Python pre-releases and may be marked as pre-releases on GitHub.

- Releases: https://github.com/getrapidkit/rapidkit-core/releases

```bash
pipx install --pip-args="--pre" rapidkit-core
# or
python -m pip install --pre -U rapidkit-core
```

## Contributing

- Start here: https://github.com/getrapidkit/rapidkit-core/tree/main/docs/contributing
- Bug reports: https://github.com/getrapidkit/rapidkit-core/issues
- Ideas and Q&A: https://github.com/getrapidkit/rapidkit-core/discussions

## License

MIT — see https://github.com/getrapidkit/rapidkit-core/blob/main/LICENSE
