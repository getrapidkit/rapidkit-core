# Troubleshooting

Catalogue common issues and diagnostics for db mongo.

## Diagnostics

- Confirm health endpoint responds:

```bash
curl -s http://localhost:8000/db-mongo/health
```

- Inspect info snapshot:

```bash
curl -s http://localhost:8000/db-mongo/info
```

- If health fails, verify `RAPIDKIT_DB_MONGO_URI` (or `config/database/db_mongo.yaml`) and network
  connectivity.
