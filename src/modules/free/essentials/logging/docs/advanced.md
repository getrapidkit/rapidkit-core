# Logging Module – Advanced Topics

This document covers advanced configuration patterns that build on the basics covered in the usage
guide.

## 1. Custom Handler Pipelines

The vendor runtime exposes factories such as `create_stream_handler`, `create_file_handler`, and
`create_syslog_handler`. Compose custom pipelines by instantiating handlers manually and registering
additional filters:

```python
from src.modules.free.essentials.logging.logging import (
    create_stream_handler,
    NoiseFilter,
)

handler = create_stream_handler("colored")
handler.addFilter(NoiseFilter())
```

Queue-based handlers can be disabled by setting `LOG_ASYNC_QUEUE=false` or globally through
`RAPIDKIT_LOGGING_FORCE_ASYNC_QUEUE` before generation.

## 2. Extending Redaction Rules

`RedactionFilter.SECRET_PATTERNS` is a tuple of compiled regular expressions. Override it at runtime
if you need to mask additional formats:

```python
from src.modules.free.essentials.logging.logging import RedactionFilter

RedactionFilter.SECRET_PATTERNS += (re.compile(r"token=[^&\s]+"),)
```

## 3. Integrating with Observability Platforms

The module ships stub handlers (`OTelBridgeHandler`, `MetricsBridgeHandler`) so projects can hook
into tracing systems. Enable them via environment defaults and implement the handler logic locally
or through overrides.

## 4. Request Context Strategy

When the FastAPI middleware is disabled (`RAPIDKIT_LOGGING_DISABLE_REQUEST_CONTEXT=true`) you can
still propagate identifiers by calling `set_request_context` manually in framework-agnostic code.

## 5. Post-Generation Snippets

Set `RAPIDKIT_LOGGING_EXTRA_SNIPPET` to a template or configuration file and optionally
`RAPIDKIT_LOGGING_EXTRA_SNIPPET_DEST` to control the destination relative to the target directory.
This is useful for seeding dashboard definitions or additional logging configuration files during
scaffolding.
