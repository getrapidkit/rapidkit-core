# RapidKit Core CLI Reference

Last updated: 2026-06-04

RapidKit Core exposes Python engine commands through `rapidkit` and `rkc`. Workspace-level workflows
are owned by the npm CLI, which may bridge into this engine when required.

## Entry Points

| Command                                     | Purpose                                       |
| ------------------------------------------- | --------------------------------------------- |
| `rapidkit`                                  | Backward-compatible Python engine entrypoint. |
| `rkc`                                       | Explicit RapidKit Core entrypoint.            |
| `npx workspai` / global `workspai` from npm | Recommended workspace CLI.                    |

## Engine Commands

```bash
rkc --help
rkc --version
rkc list
rkc frameworks
rkc doctor
rkc create project fastapi.standard my-api
rkc create project fastapi.ddd my-domain-api
rkc create project nestjs.standard my-service
```

## Module Commands

```bash
rkc modules list
rkc modules info free/essentials/settings
rkc add module free/essentials/settings
rkc add module free/auth/session --plan
rkc modules lock --overwrite
rkc modules restore --locked --ci
rkc modules restore --locked --plan --json
rkc modules install free/essentials/settings
```

Use `modules restore --locked --ci` after cloning a project that tracks `registry.json` and
`.rapidkit/modules.lock.yaml` but does not commit `.rapidkit/vendor` or `.rapidkit/snapshot`
payloads. Use `modules install` when you intentionally add or refresh module payloads during
development.

## Project Commands

Inside a generated project:

```bash
rkc init
rkc dev
rkc test
rkc lint
rkc format
rkc build
```

Project commands detect `.rapidkit/` metadata and delegate to the generated project launcher where
available.

## Maintainer Commands

The full command surface changes with the engine. For maintainers, prefer:

```bash
rkc <command> --help
python scripts/check_version_alignment.py
python scripts/sync_free_modules_registry.py
make community-dist-install
```

## Python API Stability

The CLI is the stable automation surface. Internal Python imports may change between minor versions
unless explicitly documented in a public module.

When in doubt, shell out to `rkc` or `rapidkit` from automation instead of importing internals
directly.
