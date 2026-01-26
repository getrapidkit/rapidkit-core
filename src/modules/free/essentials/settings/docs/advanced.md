````markdown
# Settings Module Advanced Topics

This guide dives into extending the generated module, wiring in custom sources, and layering
telemetry without forking the templates. Review the quick start in `usage.md` first.

## Custom dotenv management

- Extend `_append_extra_dotenv_sources` in `overrides.py` to mount extra `.env` files. The hook
  receives the generator context so you can inspect the current environment.
- Configure `RAPIDKIT_SETTINGS_EXTRA_DOTENV=".env.ci,.env.local"` to append comma-separated paths.
  The helper preserves ordering, so list the most specific files last.
- Combine dynamic sources by returning `Path` objects or callables; the override handles `str`,
  `Path`, or `(path, encoding)` tuples.

```python
from pathlib import Path


def _append_extra_dotenv_sources(builder: DotEnvBuilder) -> None:
    if env := os.getenv("CI_ENV"):  # inject per-pipeline secrets
        builder.add(Path(f".env.{env}"))
    builder.add(Path("config/.env.shared"), encoding="utf-8")
```

**Best practice:** keep production-only files in secret storage (Vault, SSM) and use dotenv for
local/dev mirrors only.

## Production validation overrides

- Set `RAPIDKIT_SETTINGS_RELAXED_ENVS="dev,ci"` (comma-separated) to disable strict guards outside
  production.
- Override `_relaxed_production_validation` to plug in custom policy engines or audit logging. The
  helper receives the instantiated `Settings` object and the current environment label.
- Ensure you keep the default production guard for `prod` to avoid missing required variables.

```python
from myapp.security import ensure_vault_tokens


def _relaxed_production_validation(settings: Settings, env_label: str) -> None:
    if env_label == "prod":
        ensure_vault_tokens(settings.VAULT_ADDR)
    else:
        logging.info("Skipping strict validation for %s", env_label)
```

**Best practice:** surface actionable errors by raising `GeneratorError` with hints instead of
generic exceptions.

## Observability hooks

- Toggle `RAPIDKIT_SETTINGS_LOG_REFRESH=1` to log refresh metadata (duration, changed keys) on every
  hot reload.
- Use `_refresh_with_observability` to emit metrics or traces. The override wraps
  `Settings.refresh()` and runs after the model is reloaded.
- Enable `RAPIDKIT_SETTINGS_TELEMETRY_ENDPOINT` to forward payloads to your logging stack. The
  default implementation integrates with the shared telemetry dispatcher when available.

```python
from rapidkit.telemetry import emit_event


def _refresh_with_observability(settings: Settings) -> None:
    emit_event(
        event="settings.refresh",
        env=settings.ENV,
        changed=settings.changed_values,
    )
```

**Best practice:** keep telemetry hooks idempotent—wrap network calls in retries and avoid blocking
the refresh loop.

## Extending generator context

Add computed values to the Jinja context by editing `generate.py` and appending keys to
`generator_context`. Example use cases include injecting feature flags into templates or enabling
optional AWS integrations. Re-run the generator and keep the vendor snapshot up-to-date with
`rapidkit modules lock`.

## Cross-module snippet providers

The settings generator consumes snippet providers declared in each module’s `config/snippets.yaml`.
This lets modules inject configuration fields or environment variables into generated outputs
without patching the base templates.

1. Add an entry to your module’s `config/snippets.yaml` that specifies the target file, anchor,
   optional profiles, and priority.
1. Place the Jinja snippet under `templates/snippets/` within the module.
1. Ensure the destination template still contains the matching anchor comment (for example
   `# <<<inject:settings-fields>>>`).
1. Run the generator or `scripts/check_module_integrity.py`; the registry merges eligible snippets
   during rendering.

Example definition:

```yaml
snippets:
  - id: redis_settings_fields
    target: src/modules/free/essentials/settings/settings.py
    anchor: "# <<<inject:settings-fields>>>"
    template: redis_fields.snippet.j2
    features: [extendable_settings, redis]
    profiles: [fastapi/standard]
    priority: 20
```

Corresponding template fragment (`templates/snippets/redis_fields.snippet.j2`):

```jinja
REDIS_URL: Optional[str] = Field(default=None, description="Redis connection URL")
REDIS_HOST: str = Field(default="localhost", description="Redis host when URL is absent")
```

Additional notes:

- Target paths are normalised automatically (with and without a leading `src/`). Use the
  comma-separated `target` list to provide any aliases the generator might produce.
- `features` and `profiles` gate injection by feature flag or framework variant; omit them to inject
  into every build.
- The snippet renderer extends the template context with `framework`, `logical_name`, and
  `target_relative_path` so snippets can adapt to their destination.
- Generated FastAPI settings call `Settings.model_rebuild()` after injection, keeping forward
  references (for example `List[...]`) introduced by snippets valid at runtime.

````
