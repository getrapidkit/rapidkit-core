# RapidKit User Guide

Last updated: 2026-06-04

RapidKit helps backend teams create workspace-based projects, install reusable modules, and keep
generated code aligned with the core engine.

For most users, the recommended entry point is the npm CLI:

```bash
npm install -g rapidkit
rapidkit --help
```

The Python package is still available for direct engine workflows:

```bash
pipx install rapidkit-core
rkc --help
```

## Create a Project

```bash
rapidkit create project fastapi.standard my-api
rapidkit create project fastapi.ddd my-domain-api
rapidkit create project nestjs.standard my-service
```

Then:

```bash
cd my-api
rapidkit init
rapidkit dev
```

## Add Modules

```bash
rapidkit modules list
rapidkit add module free/essentials/settings
rapidkit add module free/auth/session
rapidkit add module free/database/db_postgres
rapidkit add module free/ai/llm_gateway
```

Use `--plan` when you want to preview changes:

```bash
rapidkit add module free/billing/cart --plan
```

## Project Commands

Inside a generated project:

```bash
rapidkit init
rapidkit dev
rapidkit test
rapidkit lint
rapidkit format
rapidkit build
```

The CLI detects project metadata under `.rapidkit/` and delegates to the correct local runtime.

## Workspace Users

If you are building multi-project workspaces, use the npm CLI or Workspai:

- npm CLI: `https://github.com/rapidkitlabs/rapidkit-npm`
- VS Code extension: `https://github.com/rapidkitlabs/rapidkit-vscode`

The Python core remains the engine behind module and kit generation.

## Troubleshooting

| Issue                                          | Fix                                                                               |
| ---------------------------------------------- | --------------------------------------------------------------------------------- |
| `rapidkit` not found                           | Check npm global bin path or Python scripts path.                                 |
| Python core command conflicts with npm command | Prefer npm for workspace-level commands; use `rkc` for direct Python engine work. |
| dependency install stalls                      | Check network/proxy; use package mirrors only as temporary environment variables. |
| module install fails                           | Run `rapidkit modules list`, verify slug, then run with `--plan`.                 |

## Related Docs

- [Getting Started](../getting-started/README.md)
- [Modules](../modules/overview.md)
- [API Reference](../api-reference/README.md)
