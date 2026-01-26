# Troubleshooting

Catalogue common issues and diagnostics for db sqlite.

## Diagnostics

- Confirm health endpoint responds:

```bash
curl -s http://localhost:8000/db-sqlite/health
```

- Inspect tables snapshot:

```bash
curl -s http://localhost:8000/db-sqlite/tables
```

- If health fails, verify `RAPIDKIT_DB_SQLITE_PATH` (or `config/database/db_sqlite.yaml`) and
  filesystem permissions.
