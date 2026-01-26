# Ai Assistant Overview

## Mission

Deliver a provider-agnostic assistant runtime that teams can drop into FastAPI and NestJS services
to expose LLM-backed completions, structured responses, and health metadata without writing
boilerplate. The module focuses on predictable developer ergonomics (typed config, overrides) and
operational readiness (health probes + telemetry hooks).

## Capabilities

- Vendor runtime that wraps upstream LLM providers with retry, timeout, and logging policies.
- FastAPI router and NestJS module generated from the same template set to keep features in sync.
- Health helper returning structured metadata that can be shipped to observability platforms.
- Demo harness + regression tests guaranteeing Quickstart instructions stay accurate.

## Architecture

1. `generate.py` reads `module.yaml`, merges the values from `config/base.yaml`, and builds the
   render context consumed by templates.
1. Vendor templates emit `src/modules/free/ai/ai_assistant/ai_assistant.py`, health helpers, and
   typed config classes.
1. Framework plugins (FastAPI + NestJS) map context variables to framework-specific template sets.
1. Post-generation, overrides (`overrides.py`) and snippets can hook into lifecycle events to
   customize behaviour without forking templates.
1. Health + telemetry helpers are imported by default so frameworks can emit metrics, traces, and
   monitoring events with zero extra wiring.

## Observability & Telemetry

The module ships structured health probes and telemetry instrumentation:

- Health endpoints expose `version`, `uptime`, and `module` metadata for observability platforms.
- Telemetry hooks allow metric collection and distributed tracing integration.
- Request/response logging and exception telemetry integrate with standard observability systems.

## Security Posture & Audit

- **Security audit**: Regular security audits and vulnerability scans (SCA) are integrated into the
  module pipeline. Python packages are scanned via pip-audit with severity thresholds (high/critical
  fail), and Node/npm dependencies are audited for both production and development security issues.
- Provider registration flows through the runtime `validate_config` guard, which blocks duplicate
  aliases and ensures the declared default provider actually exists. This prevents spoofed provider
  entries from short-circuiting request routing.
- Safe defaults (request timeouts, disabled cache bypass, capped conversation history) mitigate
  resource exhaustion and prompt-injection style attacks that rely on unbounded context growth.
- Each framework template exposes hooks for wiring an auth layer (API keys, session tokens) so the
  generated routes can inherit the host app's security middleware instead of shipping their own.
- The stabilization suite now ships a dedicated security regression test that renders the runtime
  templates and asserts the guard rails stay intact when contributors touch the provider plumbing.
