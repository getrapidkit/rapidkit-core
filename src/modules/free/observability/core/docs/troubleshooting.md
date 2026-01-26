# Troubleshooting

## Health endpoint returns unexpected values

- Call `GET /observability-core/health` and confirm `service_name` / `environment` match your
  intended defaults.
- If you rely on generation-time overrides, ensure the relevant `RAPIDKIT_OBSERVABILITY_*` variables
  were exported **before** running the generator.

## `metrics/raw` returns JSON instead of Prometheus text

That indicates the Python runtime is using the fallback in-memory backend.

- Install the optional dependency: `prometheus_client`.
- Ensure metrics are enabled (`RAPIDKIT_OBSERVABILITY_METRICS_ENABLED=true` at generation time, or
  your config mapping sets `metrics.enabled: true`).

## Events/traces are empty

- Events only appear after you call `POST /observability-core/events` or emit them via the runtime
  facade.
- Traces only appear when tracing is enabled and spans are recorded. Verify:
  - `tracing.enabled: true` in config, and
  - sampling ratio is not `0`.

## Environment mapping values are ignored

`RAPIDKIT_OBSERVABILITY_RESOURCE_ATTRS`, `...METRICS_LABELS`, and `...METRICS_BUCKETS` support JSON
or simple comma-separated formats.

- For mappings: `{"k":"v"}` or `k=v,k2=v2`
- For bucket lists: `[0.1, 0.5, 1]` or `0.1,0.5,1`

If parsing fails, the override is skipped and defaults remain in effect.
