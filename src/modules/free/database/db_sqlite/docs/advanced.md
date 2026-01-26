# Advanced Topics

Capture extensibility hooks, override patterns, and performance considerations.

## Overrides

Generation-time overrides are applied through `overrides.py` using `RAPIDKIT_DB_SQLITE_*` variables.

For CI, consider using `:memory:` and explicit PRAGMAs for deterministic tests.
