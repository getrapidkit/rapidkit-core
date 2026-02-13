# RapidKit Core

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)

RapidKit Core is the open-source RapidKit engine + CLI.

- Install package: `rapidkit-core`

- CLI command: `rapidkit`

- Website: https://www.getrapidkit.com/

- Docs: https://www.getrapidkit.com/docs

- Repository: https://github.com/getrapidkit/rapidkit-core

- Issues: https://github.com/getrapidkit/rapidkit-core/issues

- Discussions: https://github.com/getrapidkit/rapidkit-core/discussions

## What you get

- Production-grade scaffolding for FastAPI and NestJS
- A consistent module system (add, remove, upgrade, diff)
- Project-aware commands: `init`, `dev`, `build`, `test`, `lint`, `format`

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
