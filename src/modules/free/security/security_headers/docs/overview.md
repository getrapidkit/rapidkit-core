# Security Headers Overview

The Security Headers module provides a turnkey way to attach industry-standard HTTP security headers
to every response produced by a RapidKit service. Instead of hand wiring middleware per framework,
the module ships templated adapters, vendor metadata, and health diagnostics that stay consistent
across FastAPI and NestJS projects.

## Capabilities

- Opinionated defaults for Strict-Transport-Security, Referrer-Policy, Permissions-Policy, and
  cross-origin protection headers.
- Runtime APIs for inspecting active headers, applying them to responses, and exporting health
  snapshots.
- Framework adapters that wire the runtime into FastAPI middleware and NestJS services/controllers.
- Override contracts and snippets so regulated environments can tailor policies without editing
  generated files.

## Architecture

```
┌────────────────────┐      ┌──────────────────────┐
│ templates/base/... │ ─┐  │ .rapidkit/vendor/... │
└────────────────────┘  │  └──────────────────────┘
	  │               │             │
	  ▼               │             ▼
  SecurityHeaders       │     Default vendor payloads
  (runtime facade)      │
	  │               │
	  ├───────────────┼─────┐
	  ▼               │     ▼
 FastAPI adapter     NestJS plugin
 (middleware +       (service/module/controller
 routers)            scaffolding)
```

The runtime facade handles header construction and health reporting. Framework plugins translate
that runtime into concrete outputs (Python middleware, TypeScript services) while the vendor
directory stores immutable defaults that can be reinstalled during upgrades.
