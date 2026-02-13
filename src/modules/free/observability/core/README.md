# RapidKit Observability Core Module

Cohesive metrics, tracing, and structured logging foundation for RapidKit services.

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

- Ships a cohesive runtime facade for metrics, tracing, structured logging, and lightweight event
  capture.
- Exposes transport adapters for FastAPI and NestJS so you can mount observability endpoints without
  wiring boilerplate.
- Supports Prometheus exposition on the Python runtime when `prometheus_client` is available; falls
  back to a JSON snapshot when it is not.
- Provides a health summary endpoint that reports effective configuration plus samples of recent
  spans/events.
- Keeps a vendor snapshot under `.rapidkit/vendor` so generated projects remain reproducible across
  upgrades.
- Supports environment-driven generation overrides via `overrides.py` (used to mutate the rendered
  defaults/config).

______________________________________________________________________

## Install Commands

```bash
rapidkit add module observability_core
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

`overrides.py` reads environment variables when the generator runs and uses them to mutate the
render context (`observability_defaults`). That means you can tune the generated defaults (for
example `config/observability/observability_core.yaml`) without editing templates.

Boolean variables accept: `1/0`, `true/false`, `yes/no`, `on/off` (case-insensitive).

| Environment Variable                           | Effect                                                                              |
| ---------------------------------------------- | ----------------------------------------------------------------------------------- |
| `RAPIDKIT_OBSERVABILITY_SERVICE_NAME`          | Default service name label used in metrics and health payloads.                     |
| `RAPIDKIT_OBSERVABILITY_ENVIRONMENT`           | Environment label (e.g. `local`, `staging`, `production`).                          |
| `RAPIDKIT_OBSERVABILITY_RESOURCE_ATTRS`        | Extra resource attributes. Accepts JSON (`{"key":"value"}`) or `k=v,k2=v2`.         |
| `RAPIDKIT_OBSERVABILITY_METRICS_ENABLED`       | Enable/disable metrics export in the Python runtime.                                |
| `RAPIDKIT_OBSERVABILITY_METRICS_EXPORTER`      | Exporter hint (`prometheus` is supported on Python when deps exist).                |
| `RAPIDKIT_OBSERVABILITY_METRICS_ENDPOINT`      | Logical metrics endpoint path recorded in the health summary (default `/metrics`).  |
| `RAPIDKIT_OBSERVABILITY_METRICS_NAMESPACE`     | Prometheus namespace prefix (Python runtime).                                       |
| `RAPIDKIT_OBSERVABILITY_METRICS_LABELS`        | Extra default metric labels. Accepts JSON or `k=v,k2=v2`.                           |
| `RAPIDKIT_OBSERVABILITY_METRICS_BUCKETS`       | Histogram bucket boundaries. Accepts JSON array or comma-separated floats.          |
| `RAPIDKIT_OBSERVABILITY_METRICS_RETENTION`     | Retention window in seconds (stored in config/summary; no persistence).             |
| `RAPIDKIT_OBSERVABILITY_METRICS_PROCESS`       | Register process/platform collectors when `prometheus_client` is available.         |
| `RAPIDKIT_OBSERVABILITY_TRACING_ENABLED`       | Enable/disable span capture in the Python runtime.                                  |
| `RAPIDKIT_OBSERVABILITY_TRACING_EXPORTER`      | Exporter hint (default `console`); spans are retained in memory for inspection.     |
| `RAPIDKIT_OBSERVABILITY_TRACING_ENDPOINT`      | Optional exporter endpoint (recorded in config; exporter integrations are minimal). |
| `RAPIDKIT_OBSERVABILITY_TRACING_SAMPLE_RATIO`  | Sampling ratio $0.0..1.0$ for captured spans.                                       |
| `RAPIDKIT_OBSERVABILITY_TRACING_HEADERS`       | Include incoming headers in span attributes when enabled.                           |
| `RAPIDKIT_OBSERVABILITY_LOG_LEVEL`             | Python logger level (e.g. `INFO`, `DEBUG`).                                         |
| `RAPIDKIT_OBSERVABILITY_STRUCTURED_LOGGING`    | Enable structured log formatting in the Python runtime.                             |
| `RAPIDKIT_OBSERVABILITY_INCLUDE_TRACE_IDS`     | Include trace identifiers in logs when tracing is enabled.                          |
| `RAPIDKIT_OBSERVABILITY_EVENTS_BUFFER`         | Max number of in-memory events retained by the runtime.                             |
| `RAPIDKIT_OBSERVABILITY_EVENTS_FLUSH_INTERVAL` | Flush cadence (reserved for future exporters; kept in config).                      |
| `RAPIDKIT_OBSERVABILITY_EVENTS_AUDIT`          | When enabled, emitted events are also logged via the runtime logger.                |
| `RAPIDKIT_OBSERVABILITY_RETRY_ATTEMPTS`        | Retry attempts used by helper operations (recorded in config).                      |

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
poetry run pytest tests/modules/free/observability/core -q

poetry run python scripts/check_module_integrity.py --module free/observability/core
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
