# Observability Core Overview

Observability Core provides a small, framework-friendly foundation for:

- metrics export (Prometheus on Python when optional deps are present),
- in-memory span capture (useful for local debugging and smoke tests),
- structured logging defaults,
- a lightweight event buffer with an optional audit logging toggle.

It is designed to be safe to ship in “baseline” services: you can mount its endpoints, verify that
the module is correctly configured, and increment counters/record events without requiring a full
telemetry stack.

## Capabilities

- **Metrics**: counters/gauges/histograms with sensible default labels (`service`, `environment`).
- **Tracing**: opt-in span capture with configurable sampling.
- **Events**: emit structured events and query recent entries.
- **Health summary**: a single endpoint returning effective configuration and recent samples.
- **Adapters**: FastAPI router + NestJS controller/module.

## Architecture

At runtime the module is split into three layers:

1. **Runtime facade** (`observability_core.py`): implements metrics/tracing/events and exposes
   simple helper methods (increment counter, emit event, capture spans).
1. **Transport adapters**:
   - FastAPI: router under `/observability-core/*`.
   - NestJS: controller under `/observability-core/*`.
1. **Configuration wiring**:
   - A generated YAML defaults file for FastAPI projects
     (`config/observability/observability_core.yaml`).
   - Generation-time overrides via environment variables (see `overrides.py`).

## Security considerations

- **Do not log secrets**: event attributes and span attributes may include request identifiers; keep
  them free of credentials and PII.
- **Protect endpoints**: the router/controller surfaces operational data (`/metrics`, `/events`,
  `/traces`). In production, put these behind authentication/authorization or internal networking.
- **Bounded memory**: events and spans are kept in memory with fixed maximum sizes; tune buffer
  sizes for your environment.
