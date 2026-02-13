# RapidKit Logging Module

Structured logging infrastructure with FastAPI and NestJS integrations.

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

- Vendor-backed Python runtime exporting `get_logger`, `set_request_context`, and queue-aware
  handler factories.
- Configurable formatting pipeline with JSON, plaintext, and colourised outputs, secret redaction,
  probabilistic sampling, and structured metadata enrichment.
- Optional OpenTelemetry and metrics bridge stubs for forward compatibility with tracing systems.
- FastAPI wrapper that dynamically loads the vendor payload while allowing override contracts.
- NestJS configuration module, service, schema validator, and index exports for TypeScript kits.
- Snippet catalogue injecting environment variables and documentation pointers into dependent
  modules.

______________________________________________________________________

## Install Commands

```bash
rapidkit add module logging
```

Re-run `rapidkit modules lock --overwrite` after adding or upgrading the module so downstream
projects capture the new snapshot.

### Quickstart

Follow the end-to-end walkthrough in `docs/usage.md`.

______________________________________________________________________

## Directory Layout

| Path               | Responsibility                                                              |
| ------------------ | --------------------------------------------------------------------------- |
| `module.yaml`      | Canonical metadata (version, compatibility, documentation map)              |
| `config/base.yaml` | Declarative spec that drives prompts and dependency resolution              |
| `generate.py`      | CLI/automation entry point for rendering vendor and project variants        |
| `frameworks/`      | Framework plugin implementations registered via `modules.shared.frameworks` |
| `overrides.py`     | Runtime opt-in hooks applied via environment variables                      |
| `docs/`            | Module docs referenced from `module.yaml` (usage/overview/changelog)        |
| `templates/`       | Base templates plus per-framework variants                                  |

______________________________________________________________________

## Generation Workflow

1. `generate.py` loads `module.yaml` and checks version drift with
   `modules.shared.versioning.ensure_version_consistency`.
1. Vendor artefacts are rendered from templates into `.rapidkit/vendor/...` for reproducible
   installs.
1. The requested framework plugin maps templates into project-relative paths.
1. Optional lifecycle hooks (`pre_generation_hook`, `post_generation_hook`) handle final
   adjustments.

______________________________________________________________________

## Runtime Customisation

Runtime hooks live in `overrides.py` and are toggled through environment variables:

| Environment Variable                         | Effect                                                                |
| -------------------------------------------- | --------------------------------------------------------------------- |
| `RAPIDKIT_LOGGING_FORCE_LEVEL`               | Override the default `LOG_LEVEL` fallback used in generated artefacts |
| `RAPIDKIT_LOGGING_FORCE_FORMAT`              | Force the default format (`json`, `text`, `colored`)                  |
| `RAPIDKIT_LOGGING_FORCE_SINKS`               | Provide comma-separated or JSON list of default sinks                 |
| `RAPIDKIT_LOGGING_FORCE_ASYNC_QUEUE`         | Explicitly enable/disable queue-based handlers                        |
| `RAPIDKIT_LOGGING_FORCE_REDACTION`           | Toggle secret redaction defaults                                      |
| `RAPIDKIT_LOGGING_FORCE_OTEL` / `_METRICS`   | Enable OpenTelemetry or metrics bridge handlers by default            |
| `RAPIDKIT_LOGGING_DISABLE_REQUEST_CONTEXT`   | Remove the request context middleware from generated FastAPI wrappers |
| `RAPIDKIT_LOGGING_EXTRA_SNIPPET` (+ `_DEST`) | Copy an additional snippet into the generated project after rendering |

See the `LoggingOverrideState` dataclass for the complete list of knobs.

______________________________________________________________________

## Security & Audit

This module ships as part of the RapidKit module ecosystem and is intended to be **audited** as a
unit:

- Use `scripts/modules_doctor.py` (or `rapidkit modules vet`) to validate structure and generator
  invariants.
- Use `rapidkit modules verify-all` to verify recorded hashes/signatures when running in release
  mode.

If you extend this module, keep the documentation updated with the security assumptions and any
threat model relevant to your deployment.

______________________________________________________________________

## Testing Checklist

```bash
poetry run pytest tests/modules/free/essentials/logging -q

poetry run python scripts/check_module_integrity.py --module free/essentials/logging
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

For additional help, open an issue at <https://github.com/getrapidkit/rapidkit-core/issues> or
consult the full product documentation at <https://docs.rapidkit.top>.
