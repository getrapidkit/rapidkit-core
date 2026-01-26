# Usage

This guide shows how to generate the Db Mongo module and wire it into a FastAPI or NestJS app.

## Quickstart (FastAPI)

1. Install the module

   ```bash
   rapidkit add module db_mongo
   rapidkit modules lock --overwrite
   ```

1. Generate the FastAPI variant

   ```bash
   poetry run python -m src.modules.free.database.db_mongo.generate fastapi ./tmp/db_mongo
   rsync -a ./tmp/db_mongo/ ./
   ```

1. Register the routes

   ```python
   from fastapi import FastAPI
   from src.modules.free.database.db_mongo.db_mongo import register_fastapi

   app = FastAPI()
   register_fastapi(app)
   ```

1. Try the HTTP surface

   ```bash
   curl http://localhost:8000/db-mongo/health
   curl http://localhost:8000/db-mongo/info
   ```

## Quickstart (NestJS)

1. Install + lock

   ```bash
   rapidkit add module db_mongo
   rapidkit modules lock --overwrite
   ```

1. Generate the NestJS variant

   ```bash
   poetry run python -m src.modules.free.database.db_mongo.generate nestjs ./tmp/db_mongo
   rsync -a ./tmp/db_mongo/ ./
   ```

1. Import the module

   ```ts
   import { Module } from '@nestjs/common';
   import { DbMongoModule } from './modules/free/database/db_mongo/db-mongo/db-mongo.module';

   @Module({
     imports: [DbMongoModule],
   })
   export class AppModule {}
   ```

## Configuration

- FastAPI scaffolds defaults into `config/database/db_mongo.yaml`.
- For local development, set a connection URI (or update the config file), for example:
  `mongodb://localhost:27017`.

If you need a different default without editing generated files, set generation-time overrides
before running the generator (see the README `Runtime Customisation` section).

## Endpoints (FastAPI)

- `GET /db-mongo/health`
- `GET /db-mongo/info`
