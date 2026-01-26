# Api Keys Overview

The Api Keys module provides a small runtime facade and framework adapters for issuing and verifying
API keys in a consistent way across projects.

## Capabilities

- Issue keys for an owner with optional TTL, labels, and metadata.
- Verify presented tokens against required scopes.
- Revoke keys and emit audit entries.
- Expose lightweight health + metadata payloads for `src/health` aggregation.

## Architecture

- Core runtime lives under `src/modules/free/auth/api_keys/api_keys.py`.
- FastAPI adapter provides an `APIRouter` via `build_router()`.
- The router includes `/api_keys/metadata` and `/api_keys/health` endpoints.
- Configuration defaults are generated to `config/api_keys.yaml` and can be overridden via
  `overrides.py`.

## Security considerations

This module touches privileged access paths; treat tokens and hashing secrets as sensitive.

- Security: store only derived token material (never persist plaintext secrets) and keep the hashing
  pepper out of source control.
- Threat model: plan for key stuffing/replay, scope escalation attempts, and brute-force
  verification.
- Audit: enable audit trails for issuance/verification/revocation events and define retention and
  access controls.
