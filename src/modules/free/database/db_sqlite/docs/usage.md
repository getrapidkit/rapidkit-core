# Usage

This guide shows how to generate the Db Sqlite module and wire it into a FastAPI or NestJS app.

## Quickstart (FastAPI)

1. Install the module

   ```bash
   rapidkit add module db_sqlite
   rapidkit modules lock --overwrite
   ```

1. Generate the FastAPI variant

   ```bash
   poetry run python -m src.modules.free.database.db_sqlite.generate fastapi ./tmp/db_sqlite
   rsync -a ./tmp/db_sqlite/ ./
   ```

1. Register the routes

   ```python
   from fastapi import FastAPI
   from src.modules.free.database.db_sqlite.db_sqlite import register_fastapi

   app = FastAPI()
   register_fastapi(app)
   ```

1. Try the HTTP surface

   ```bash
   curl http://localhost:8000/db-sqlite/health
   curl http://localhost:8000/db-sqlite/tables
   ```

## Quickstart (NestJS)

1. Install + lock

   ```bash
   rapidkit add module db_sqlite
   rapidkit modules lock --overwrite
   ```

1. Generate the NestJS variant

   ```bash
   poetry run python -m src.modules.free.database.db_sqlite.generate nestjs ./tmp/db_sqlite
   rsync -a ./tmp/db_sqlite/ ./
   ```

1. Import the module

   ```ts
   import { Module } from '@nestjs/common';
   import { DbSqliteModule } from './modules/free/database/db_sqlite/db-sqlite/db-sqlite.module';

   @Module({
     imports: [DbSqliteModule],
   })
   export class AppModule {}
   ```

## Configuration

- FastAPI scaffolds defaults into `config/database/db_sqlite.yaml`.
- The default database path is typically `./.rapidkit/runtime/sqlite/app.db`.

If you need a different default without editing generated files, set generation-time overrides
before running the generator (see the README `Runtime Customisation` section).

## Endpoints (FastAPI)

- `GET /db-sqlite/health`
- `GET /db-sqlite/tables`
