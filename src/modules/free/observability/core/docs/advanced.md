# Advanced Topics

## Override patterns

Observability Core supports **generation-time overrides** via `overrides.py`. The generator reads
the `RAPIDKIT_OBSERVABILITY_*` environment variables and mutates the `observability_defaults`
context used to render configuration and templates.

Recommended workflow:

1. Export overrides for the environment you are generating for (dev/stage/prod).
1. Run the generator.
1. Commit only sane defaults (avoid secrets), and set sensitive values at deploy time.

## Custom metrics and labels

The Python runtime exposes helper calls like `increment_counter`, `set_gauge`, and
`observe_histogram`. Standardise metric names and label keys early:

- Metric names: `requests_total`, `request_latency_seconds`, `cache_hits_total`.
- Labels: `service`, `environment`, plus stable dimensions such as `route` or `status_code`.

Keep label cardinality bounded (avoid `user_id`, `email`, etc.).

## Tracing notes

Span capture is designed for lightweight inspection. When enabled, spans are retained in memory and
exposed via `/observability-core/traces`.

Use sampling (`tracing.sample_ratio`) to avoid excessive overhead.
