# RapidKit Rate Limiting Module

Request rate limiting and throttling protections for RapidKit services

This README follows the shared RapidKit module format:

1. **Overview & capabilities**
1. **Installation commands**
1. **Directory layout**
1. **Generation workflow**
1. **Runtime customisation hooks**
1. **Testing & release checklist**
1. **Reference links**

Use the same headings when documenting other modules so maintainers know what to expect.

As a RapidKit module, this module also follows the shared metadata/documentation standard:

- `module.yaml` is the canonical source of truth (including the `documentation:` map).
- Module docs live under `docs/` and should match the keys referenced from `module.yaml`.
- The module changelog is maintained in `docs/changelog.md` and referenced both from `module.yaml`
  and this README.

______________________________________________________________________

## Module Capabilities

- Memory and Redis backends with consistent semantics across Python and TypeScript runtimes.
- Declarative rules with path/method matching, scopes (`global`, `identity`, `route`,
  `route-identity`), optional blocking windows, and weighted costs.
- FastAPI middleware + dependency helpers delivering 429 responses, standard rate limit headers, and
  pluggable identity resolution.
- NestJS service exposing the same policy definitions with response header helpers for controllers
  and guards.
- Environment-driven configuration (JSON rules, header overrides, Redis prefixing) plus snippet
  injection for `.env` files.
- Overrides contract enabling install-time mutation of defaults, additional rules, or snippet
  augmentation.

______________________________________________________________________

- Usage guide: `docs/usage.md`
- Advanced scenarios: `docs/advanced.md`
- Migration playbook: `docs/migration.md`
- Troubleshooting: `docs/troubleshooting.md`

# Regenerate snippets & vendor assets

rapidkit modules lock --overwrite

````

Ensure Redis is reachable if you plan to switch to the Redis backend. The
module defaults to the in-process memory backend for single-node deployments.

______________________________________________________________________

## Install Commands

```bash
rapidkit add module rate_limiting
```

Re-run `rapidkit modules lock --overwrite` after adding or upgrading the module so downstream
projects capture the new snapshot.

### Quickstart

Follow the end-to-end walkthrough in `docs/usage.md`.

______________________________________________________________________

## Directory Layout

| Path                     | Responsibility                                                       |
| ------------------------ | -------------------------------------------------------------------- |
| `module.yaml`            | Canonical metadata (version, compatibility, documentation map)       |
| `config/base.yaml`       | Declarative spec that drives prompts and dependency resolution       |
| `generate.py`            | CLI/automation entry point for rendering vendor and project variants |
| `frameworks/`            | Framework plugin implementations registered via `modules.shared.frameworks` |
| `overrides.py`           | Runtime opt-in hooks applied via environment variables               |
| `docs/`                  | Module docs referenced from `module.yaml` (usage/overview/changelog) |
| `templates/`             | Base templates plus per-framework variants                           |

______________________________________________________________________

## Generation Workflow

1. `generate.py` loads `module.yaml` and checks version drift with `modules.shared.versioning.ensure_version_consistency`.
1. Vendor artefacts are rendered from templates into `.rapidkit/vendor/...` for reproducible installs.
1. The requested framework plugin maps templates into project-relative paths.
1. Optional lifecycle hooks (`pre_generation_hook`, `post_generation_hook`) handle final adjustments.

______________________________________________________________________

## Runtime Customisation

### Environment Variables

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `RATE_LIMIT_ENABLED` | `true` | Toggle runtime enforcement. |
| `RATE_LIMIT_BACKEND` | `memory` | Backend driver (`memory` or `redis`). |
| `RATE_LIMIT_REDIS_URL` | `redis://localhost:6379/2` | Redis connection string when using the distributed backend. |
| `RATE_LIMIT_REDIS_PREFIX` | `rate-limit` | Namespace prefix applied to Redis keys. |
| `RATE_LIMIT_DEFAULT_LIMIT` | `120` | Requests allowed in the default window. |
| `RATE_LIMIT_DEFAULT_WINDOW` | `60` | Window length (seconds) for the default rule. |
| `RATE_LIMIT_DEFAULT_SCOPE` | `identity` | Default scope (`global`, `identity`, `route`, `route-identity`). |
| `RATE_LIMIT_DEFAULT_BLOCK_SECONDS` | _unset_ | Optional hard block applied once the limit is exceeded. |
| `RATE_LIMIT_RULES_JSON` | _unset_ | JSON array describing additional rules (name, limit, window, routes, methods, etc.). |
| `RATE_LIMIT_HEADER_*` | See defaults | Override emitted header names (limit, remaining, reset, retry-after, rule). |

### Overrides Contract

`RateLimitingOverrides` allows teams to:

- Override default rule metadata (limits, windows, scopes) based on install
  context.
- Inject additional snippet sources into generated projects.
- Hook into variant generation pre/post phases for advanced manipulation.

______________________________________________________________________

## Security & Audit

This module ships as part of the RapidKit module ecosystem and is intended to be **audited** as a unit:

- Use `scripts/modules_doctor.py` (or `rapidkit modules vet`) to validate structure and generator invariants.
- Use `rapidkit modules verify-all` to verify recorded hashes/signatures when running in release mode.

If you extend this module, keep the documentation updated with the security assumptions and any threat model
relevant to your deployment.

______________________________________________________________________

## Testing Checklist

```bash
poetry run pytest tests/modules/free/security/rate_limiting -q

poetry run python scripts/check_module_integrity.py --module free/security/rate_limiting
```

______________________________________________________________________

## Release Checklist

1. Update templates and/or `module.yaml`.
1. Regenerate vendor snapshots and project variants for every supported framework.
1. Inspect rendered files (`.rapidkit/vendor` and sample project outputs) for accuracy.
1. Execute the testing checklist above; ensure versioning is bumped when content hashes change.
1. Commit regenerated assets alongside the updated metadata.

______________________________________________________________________

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

For additional help, open an issue at <https://github.com/getrapidkit/rapidkit-core/issues> or consult the
full product documentation at <https://docs.rapidkit.top>.
````
