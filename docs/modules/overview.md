# RapidKit Modules Overview

Last updated: 2026-06-04

RapidKit modules are reusable backend capabilities that can be installed into generated projects.
The current free catalog contains 52 stable modules under `src/modules/free`.

## Source of Truth

- Module directories: `src/modules/free/<category>/<slug>/`
- Module manifest: `module.yaml`
- Optional aggregate registry: `src/modules/free/modules.yaml`
- Runtime snippets: `config/snippets.yaml` and `templates/snippets/`
- Stabilization evidence: `dev-engine/audit-history/`

The per-module `module.yaml` is the canonical dependency and generation contract. The aggregate
`modules.yaml` is a listing/registry artifact and should be regenerated after module changes.

## Supported Release Kits

- `fastapi.standard`
- `fastapi.ddd`
- `nestjs.standard`

Compatibility is proven through stabilization gates, not static claims alone. Use
`make stabilize-release <category>` or `make stabilize-release-all` before calling a module
customer-ready.

## Install Modules

Inside a generated project:

```bash
rapidkit add module free/essentials/settings
rapidkit add module free/auth/session
rapidkit add module free/ai/llm_gateway --plan
```

The CLI resolves dependencies from manifests, renders templates, applies snippets, updates RapidKit
metadata, and records drift information for future updates.

## Restore Clean Clones

Cloneable projects should track `registry.json` and `.rapidkit/modules.lock.yaml`, not generated
`.rapidkit/vendor/**` or `.rapidkit/snapshot/**` payloads. After cloning, restore the exact locked
module payloads with:

```bash
rapidkit modules restore --locked --ci
```

Use `rapidkit modules restore --locked --plan --json` in CI or release checks to verify the restore
contract without writing payload files.

## Standard Module Shape

```text
src/modules/free/<category>/<slug>/
  module.yaml
  generate.py
  overrides.py
  README.md
  docs/
    changelog.md
  config/
    base.yaml
    snippets.yaml
  templates/
    base/
    variants/
      fastapi/
      nestjs/
    snippets/
```

Some modules intentionally omit framework variants or runtime files, but that choice must be
reflected in the manifest, docs, and tests.

## Quality Gates

```bash
python scripts/sync_free_modules_registry.py
poetry run pytest -q tests/modules/test_module_consistency.py
make stabilize-fast <category>
make stabilize-shared <category>
make stabilize-release <category>
```

Use shared integration for workflow modules such as events, queues, webhooks, billing, approvals,
and support flows.

## Categories

- `ai`
- `auth`
- `billing`
- `business`
- `cache`
- `communication`
- `database`
- `essentials`
- `observability`
- `security`
- `tasks`
- `users`

## Enterprise Readiness

A module is enterprise-ready when generated code is useful without manual patching, failure modes
are explicit, docs are actionable, and every supported kit has current evidence under
`dev-engine/audit-history/`.
