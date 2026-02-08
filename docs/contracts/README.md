# RapidKit CLI Contracts

This directory defines the **stable JSON contracts** emitted by RapidKit Core CLI commands. These
contracts are used by the npm bridge and other tooling to ensure compatibility.

## Schemas

- `rapidkit-cli-contracts.json`
  - `VersionResponse` — output of `rapidkit version --json`
  - `CommandsResponse` — output of `rapidkit commands --json`
  - `ProjectDetectResponse` — output of `rapidkit project detect --json`
  - `ModulesListResponseV1` — output of `rapidkit modules list --json-schema 1`

## Versioning

- Each payload includes `schema_version`.
- Backward-compatible changes must keep `schema_version` unchanged.
- Breaking changes must increment `schema_version` **and** update npm bridge tests.

## Tests

Core validates these contracts in:

- `tests/cli/test_cli_contracts.py`
