# API Reference

This module exposes a small HTTP surface for inspection and smoke testing. All endpoints are mounted
under the module prefix:

- `/observability-core/*`

## FastAPI Endpoints

### `GET /observability-core/health`

Returns an `ObservabilitySummary` payload with effective configuration and small samples.

### `GET /observability-core/metrics`

Returns an `ObservabilityMetricSnapshot`:

```json
{
	"payload": "...",
	"content_type": "text/plain"
}
```

### `GET /observability-core/metrics/raw`

Returns the raw exposition body.

- When `prometheus_client` is installed and enabled, the response is Prometheus text format.
- Otherwise, the response is a JSON payload rendered by the fallback in-memory backend.

### `GET /observability-core/events?limit=50`

Returns recent buffered events.

### `POST /observability-core/events`

Body (`ObservabilityEventCreate`):

```json
{
	"name": "user.signup",
	"severity": "INFO",
	"attributes": {"source": "api"}
}
```

Response (`ObservabilityEvent`): includes a `timestamp`.

### `GET /observability-core/traces?limit=25`

Returns recent captured spans (`ObservabilitySpan`).

## NestJS Endpoints

The NestJS adapter exposes the same logical endpoints (except `/metrics/raw`). The `metrics`
response is always JSON and uses `contentType: "application/json"`.

## Data Contracts

The Python adapter uses Pydantic models generated in `types/observability_core.py`:

- `ObservabilitySummary`: `{ module, status, service_name, environment, metrics, tracing, events }`
- `ObservabilityMetricSnapshot`: `{ payload, content_type }`
- `ObservabilityEventCreate`: `{ name, severity, attributes }`
- `ObservabilityEvent`: `{ name, severity, attributes, timestamp }`
- `ObservabilitySpan`: `{ name, duration_ms, attributes }`

Treat event/span `attributes` as untrusted input: validate and redact as needed.
