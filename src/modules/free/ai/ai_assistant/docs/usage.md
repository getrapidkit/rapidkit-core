# Ai Assistant Usage Guide

## Quickstart

1. Add the module to your workspace and install dependencies:

   ```bash
   rapidkit add module ai_assistant
   poetry install
   ```

1. Generate the vendor runtime plus FastAPI integration into a sandbox directory:

   ```bash
   poetry run python -m src.modules.free.ai.ai_assistant.generate fastapi ./tmp/ai_assistant_fastapi
   ```

1. Add your provider API key (for example `OPENAI_API_KEY`) and include the generated router inside
   your FastAPI app:

   ```python
   from fastapi import FastAPI
   from src.modules.free.ai.ai_assistant.routers.ai import ai_assistant

   app = FastAPI()
   app.include_router(ai_assistant.build_router())
   app.include_router(ai_assistant.build_health_router())
   ```

1. Launch `uvicorn main:app --reload` and issue a request to `POST /ai/assistant/completions` or
   `GET /ai/assistant/health` to verify the runtime wiring.

`src/modules/free/ai/ai_assistant/scripts/run_demo.py` encapsulates the same workflow and can be
executed in CI to guarantee the templates keep producing runnable projects.

### NestJS

1. Generate the NestJS variant into your workspace:

   ```bash
   poetry run python -m src.modules.free.ai.ai_assistant.generate nestjs ./tmp/ai_assistant_nest
   ```

1. Import the generated module and controller:

   ```ts
   import { Module } from "@nestjs/common";
   import { AiAssistantModule } from "./ai-assistant/ai_assistant.module";

   @Module({ imports: [AiAssistantModule.forRoot()] })
   export class AppModule {}
   ```

1. Start the NestJS server and call `POST /ai/assistant/completions` or `POST /ai/assistant/stream`
   to fetch responses. `GET /ai/assistant/health` mirrors the vendor telemetry payload so
   observability dashboards stay aligned across frameworks.

## Configuration

Configuration defaults live in `config/base.yaml` so you can override them via environment variables
or static context:

| Key / Env Var                                                 | Default | Notes                                                   |
| ------------------------------------------------------------- | ------- | ------------------------------------------------------- |
| `log_level` / `RAPIDKIT_AI_ASSISTANT_LOG_LEVEL`               | `INFO`  | Adjusts logging verbosity for the runtime + routers     |
| `request_timeout_seconds` / `RAPIDKIT_AI_ASSISTANT_TIMEOUT`   | `30`    | Timeout applied to outbound LLM calls                   |
| `feature_flag_enabled` / `RAPIDKIT_AI_ASSISTANT_FEATURE_FLAG` | `false` | Example feature gate toggled inside generated templates |

Use overrides in `overrides.py` when you need to patch behaviour without re-rendering the module.

## Health, Monitoring, and Telemetry

- `src/health/ai_assistant.py` exposes `check_health` which returns structured metadata (status,
  region, retry policy). Forward this payload to your monitoring stack for dashboards.
- The generated FastAPI router emits structured logs for each completion request; wire those logs
  into your preferred telemetry sink (Grafana, Datadog, etc.).
- Wrap the runtime with the provided middleware hooks to export Prometheus metrics such as request
  duration or tokens processed. The templates already import `time.perf_counter` to make adding
  counters straightforward.

## Framework Examples

### FastAPI

1. Import the router from `src.modules.free.ai.ai_assistant.routers.ai.ai_assistant`.
1. Include the endpoints with `app.include_router(ai_assistant.build_router())`.
1. Include the health endpoint with `app.include_router(ai_assistant.build_health_router())`.

### NestJS

1. Generate the NestJS variant with
   `poetry run python -m src.modules.free.ai.ai_assistant.generate nestjs ./tmp`.
1. Import `AiAssistantModule` inside your NestJS root module and expose the controller or gRPC
   service exported from `src/modules/free/ai/ai_assistant/ai-assistant`.
1. Pipe metrics to your telemetry pipeline by decorating the generated service methods with the
   shared `MonitoringService` that ships in the NestJS kit.
