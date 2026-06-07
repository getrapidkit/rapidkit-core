# RapidKit Event Bus Module

In-process event bus with subscriptions, durable-style event records, replay, and dead-letter
semantics.

This module is part of the free RapidKit product-factory layer used to build production-grade
workspace products for FastAPI and NestJS. It follows the shared module contract: manifest-driven
metadata, framework-specific generation, vendor snapshots, health hooks, override support,
documentation, snippets, and module-scoped tests.

This README follows the shared RapidKit module format so maintainers can review capabilities,
generation behavior, runtime controls, security assumptions, and release readiness without opening
every template file.

## Module Capabilities

- Provides a consistent publish/subscribe boundary for product events.
- Captures event metadata required for replay and troubleshooting.
- Supports dead-letter style handling for failed subscribers.
- Keeps domain workflows decoupled from transport details.

## Install Commands

```bash
rapidkit add module event_bus
rapidkit modules lock --overwrite
```

Use the canonical slug when scripting installs:

```bash
rapidkit add module free/tasks/event_bus
```

## Quickstart

1. Define stable event names and payload schemas.
1. Publish after durable state changes, not before.
1. Make subscribers idempotent by event ID.
1. Review dead-letter records during operational incidents.

## Directory Layout

| Path                          | Responsibility                                                             |
| ----------------------------- | -------------------------------------------------------------------------- |
| `module.yaml`                 | Canonical metadata, dependencies, compatibility, testing, and docs map     |
| `config/base.yaml`            | Module variables, profiles, and dependency declarations                    |
| `config/snippets.yaml`        | Snippet bundle registration                                                |
| `generate.py`                 | Vendor and framework variant generator                                     |
| `frameworks/`                 | FastAPI and NestJS plugin adapters                                         |
| `templates/base/`             | Shared vendor runtime templates                                            |
| `templates/variants/fastapi/` | FastAPI runtime, health, router, and E2E templates                         |
| `templates/variants/nestjs/`  | NestJS service, controller, module, health, validation, and E2E templates  |
| `templates/snippets/`         | Reusable insertion snippets for generated projects                         |
| `docs/`                       | Overview, usage, monitoring, migration, troubleshooting, and API reference |

## Generation Workflow

1. `generate.py` loads `module.yaml`, `config/base.yaml`, and framework plugin metadata.
1. Shared vendor templates render into `.rapidkit/vendor/...` for reproducible installs.
1. FastAPI and NestJS variants map framework files into the target workspace.
1. Health, snippets, and override contracts are generated alongside runtime code.
1. Module tests and validators confirm the rendered output remains upgrade-safe.

## Demo And Smoke Checks

Use the module demo runner to inspect generated output before promoting template changes:

```bash
python scripts/run_demo.py fastapi
python scripts/run_demo.py nestjs
```

For release validation, compare the generated FastAPI and NestJS projects with the module's expected
outputs, then run the module-scoped test and validator commands in the testing checklist below.

## Runtime Customisation

| Environment Variable                   | Effect                                                   |
| -------------------------------------- | -------------------------------------------------------- |
| `RAPIDKIT_EVENT_BUS_ENABLED`           | Enables generated event bus services.                    |
| `RAPIDKIT_EVENT_BUS_REPLAY_MODE`       | Controls disabled, admin-only, or audit replay behavior. |
| `RAPIDKIT_EVENT_BUS_DEAD_LETTER_LIMIT` | Maximum retained failed event records.                   |

Override contracts live in `overrides.py`. Keep custom behavior behind those hooks so product
workspaces can upgrade the module without forking template internals.

## Security & Audit

- Validate event payload schemas before dispatch.
- Restrict replay to trusted operators with reason capture.
- Avoid sending secrets or raw regulated payloads through generic events.

Every production workspace should route privileged changes through audit policy, emit structured
logs, and include tenant/user correlation IDs when this module is used in a multi-tenant product.

## Enterprise Operations

| Area        | Production expectation                                                                                 |
| ----------- | ------------------------------------------------------------------------------------------------------ |
| Ownership   | Assign an owning team for configuration, rollout decisions, and incident response.                     |
| Metrics     | Track request/job counts, latency, failure rates, retries, and policy-denied operations.               |
| Audit       | Record actor, tenant, target, reason, correlation ID, and before/after state for privileged mutations. |
| Idempotency | Use stable operation IDs for retries, replays, imports, webhooks, billing events, and background work. |
| Rollback    | Keep previous config/templates deployable and document the rollback command or operator action.        |

## Failure Modes

- Dependency outage: fail closed for authorization, billing, and safety decisions; otherwise degrade
  with clear health status.
- Partial execution: record the last durable state before retrying or replaying side effects.
- Duplicate event or job: deduplicate by operation ID before mutating state.
- Tenant mismatch: reject the operation and emit an audit/security event.
- Configuration drift: run module validators and compare generated manifests before release.

## Testing Checklist

```bash
poetry run pytest tests/modules/free/tasks/event_bus -q
poetry run python -m modules.free.tasks.event_bus.generate fastapi ./tmp/event_bus-fastapi
poetry run python -m modules.free.tasks.event_bus.generate nestjs ./tmp/event_bus-nestjs
poetry run python scripts/validate_module_structure.py free/tasks/event_bus
poetry run python scripts/validate_module_docs_quality.py --module free/tasks/event_bus
poetry run python scripts/validate_module_snippet_configs.py --module free/tasks/event_bus
```

## Release Checklist

1. Update `module.yaml`, templates, docs, and snippets together.
1. Run docs, README, structure, and snippet validators before publishing.
1. Run FastAPI and NestJS generator smoke tests.
1. Sync module metadata, verify hashes, and refresh the free registry.
1. Re-run the product-factory coverage matrix before using the module in a workspace product.
1. Confirm security, support, and rollback notes are still accurate for both supported frameworks.

## Reference Documentation

- Overview: `docs/overview.md`
- Usage guide: `docs/usage.md`
- Advanced scenarios: `docs/advanced.md`
- Monitoring: `docs/monitoring.md`
- Changelog: `docs/changelog.md`
- Migration playbook: `docs/migration.md`
- Troubleshooting: `docs/troubleshooting.md`
- API reference: `docs/api-reference.md`
- Override contracts: `overrides.py`

Category: `tasks` Canonical slug: `free/tasks/event_bus`
