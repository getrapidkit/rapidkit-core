# API Reference

Describe HTTP endpoints, CLI commands, request/response schemas, and integration contracts for
stripe payment.

## Endpoints

- `GET /stripe-payment/health`: readiness snapshot.
- `GET /stripe-payment/metadata`: configuration + environment metadata.

## Data Contracts

- Health payload includes `status`, `environment`, and retry policy details.
- Security: never return secrets; only return booleans/metadata.
