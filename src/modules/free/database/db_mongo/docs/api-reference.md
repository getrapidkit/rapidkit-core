# API Reference

Describe HTTP endpoints, CLI commands, request/response schemas, and integration contracts for db
mongo.

## Endpoints

- `GET /db-mongo/health`: connectivity + timeout diagnostics.
- `GET /db-mongo/info`: server info snapshot for operator troubleshooting.

## Data Contracts

- Health payload includes `status` and timing metadata.
- Info payload includes safe server/driver metadata.
- Security: do not return credentials; protect `/info` behind auth in production.
