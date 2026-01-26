# API Reference

Describe HTTP endpoints, CLI commands, request/response schemas, and integration contracts for db
sqlite.

## Endpoints

- `GET /db-sqlite/health`: connectivity + timeout diagnostics.
- `GET /db-sqlite/tables`: quick schema/table snapshot.

## Data Contracts

- Health payload includes `status` and timing metadata.
- Tables payload returns a list of table names.
- Security: protect schema endpoints in production-like environments.
