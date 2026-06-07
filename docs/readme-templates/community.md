# RapidKit Core

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Part of RapidKit Platform](https://img.shields.io/badge/Part%20of-RapidKit%20Workspace%20Platform-0f172a?logo=github)](https://github.com/rapidkitlabs/rapidkit)

RapidKit Core is the open-source RapidKit engine and CLI for scaffolding, operating, and evolving
production-ready backend projects.

- Package: `rapidkit-core`
- CLI: `rapidkit` (Core aliases: `rapidkit-core`, `rkc`)
- Website: https://www.getrapidkit.com/
- Docs: https://www.getrapidkit.com/docs
- Repository: https://github.com/rapidkitlabs/rapidkit-core
- Issues: https://github.com/rapidkitlabs/rapidkit-core/issues
- Discussions: https://github.com/rapidkitlabs/rapidkit-core/discussions

## Part of the RapidKit Ecosystem

This repository is the core engine layer of the broader **RapidKit Platform**:

| Layer         | Repository                                                                                                                                                                    |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Ecosystem Hub | [rapidkitlabs/rapidkit](https://github.com/rapidkitlabs/rapidkit)                                                                                                             |
| CLI           | [rapidkitlabs/rapidkit-npm](https://github.com/rapidkitlabs/rapidkit-npm) · [npm](https://www.npmjs.com/package/rapidkit)                                                     |
| IDE           | [rapidkitlabs/rapidkit-vscode](https://github.com/rapidkitlabs/rapidkit-vscode) · [Marketplace](https://marketplace.visualstudio.com/items?itemName=rapidkit.rapidkit-vscode) |
| Examples      | [rapidkitlabs/rapidkit-examples](https://github.com/rapidkitlabs/rapidkit-examples)                                                                                           |

## What you get

- Production-grade scaffolding for FastAPI and NestJS
- Stable module lifecycle: add, remove, upgrade, diff, reconcile, rollback
- Project-aware commands for local development and CI workflows
- Standardized project structure with `.rapidkit/` metadata
- Enterprise-oriented quality gates across metadata, docs, tests, and release checks

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

## Recommended Professional Start Path

For most teams, the best developer experience is:

1. Start from the npm CLI layer:
   - CLI repo: `https://github.com/rapidkitlabs/rapidkit-npm`
   - npm: https://www.npmjs.com/package/rapidkit
1. Install/update the Python engine package (`rapidkit-core`) for module generation/runtime parity.
1. Use the VS Code extension when you want the full graphical + AI workspace experience:
   - Extension repo: `https://github.com/rapidkitlabs/rapidkit-vscode`
   - Marketplace: https://marketplace.visualstudio.com/items?itemName=rapidkit.rapidkit-vscode

The VS Code extension positioning: "The AI workspace for backend teams. Build backend systems with
AI that knows your workspace, generate projects and modules from intent, debug with full context,
and ship faster — all inside VS Code."

## Core Kits

Current primary kits in RapidKit Core:

- `fastapi.standard`
- `fastapi.ddd`
- `nestjs.standard`

Source directories:

- `src/kits/fastapi/standard`
- `src/kits/fastapi/ddd`
- `src/kits/nestjs/standard`

## Free Modules Catalog (52)

This community channel currently ships 52 stable free modules. Source of truth:
`src/modules/free/modules.yaml`

| Category      | Count | Modules                                                                                                                                                                                                                  |
| ------------- | ----: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| AI            |     8 | `agent_runtime`, `ai_assistant`, `ai_guardrails`, `llm_gateway`, `prompt_ops`, `rag_pipeline`, `tool_registry`, `vector_store`                                                                                           |
| Auth          |     5 | `api_keys`, `auth_core`, `oauth`, `passwordless`, `session`                                                                                                                                                              |
| Billing       |     4 | `cart`, `inventory`, `stripe_payment`, `usage_billing`                                                                                                                                                                   |
| Business      |    12 | `admin_console`, `approval_engine`, `connector_hub`, `connector_pack_library`, `document_pipeline`, `feature_flags`, `forms_engine`, `media_pipeline`, `multi_tenancy`, `org_admin_console`, `storage`, `support_center` |
| Cache         |     1 | `redis`                                                                                                                                                                                                                  |
| Communication |     3 | `email`, `notifications`, `webhook_platform`                                                                                                                                                                             |
| Database      |     3 | `db_mongo`, `db_postgres`, `db_sqlite`                                                                                                                                                                                   |
| Essentials    |     4 | `deployment`, `logging`, `middleware`, `settings`                                                                                                                                                                        |
| Observability |     2 | `analytics_dashboard`, `observability_core`                                                                                                                                                                              |
| Security      |     4 | `audit_policy`, `cors`, `rate_limiting`, `security_headers`                                                                                                                                                              |
| Tasks         |     4 | `celery`, `event_bus`, `queue_platform`, `workflow_engine`                                                                                                                                                               |
| Users         |     2 | `users_core`, `users_profiles`                                                                                                                                                                                           |

To refresh the free registry after module changes:

```bash
python scripts/sync_free_modules_registry.py
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

- Releases: https://github.com/rapidkitlabs/rapidkit-core/releases

```bash
pipx install --pip-args="--pre" rapidkit-core
# or
python -m pip install --pre -U rapidkit-core
```

## Stability and Release Policy

- `rapidkit-core` community channel is intended to be stable for production use.
- New module capabilities are introduced with metadata/version bumps and compatibility checks.
- Release readiness is validated through tests, structure checks, snippet checks, and module health
  scoring.
- For RC testing and pre-release validation, use the staging channel template
  (`community-staging.md`).

## Contributing

- Start here: https://github.com/rapidkitlabs/rapidkit-core/tree/main/docs/contributing
- Bug reports: https://github.com/rapidkitlabs/rapidkit-core/issues
- Ideas and Q&A: https://github.com/rapidkitlabs/rapidkit-core/discussions

For local source development in this repository:

```bash
make install-dev
make test
```

## License

MIT — see https://github.com/rapidkitlabs/rapidkit-core/blob/main/LICENSE
