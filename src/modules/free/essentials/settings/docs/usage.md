# Settings Module Usage

The settings module provides a shared, multi-framework configuration layer for RapidKit projects.
This guide walks through installation, runtime integration, recommended tests, and the public APIs
exposed by the module.

## Prerequisites

- Python 3.10+
- RapidKit CLI (`rapidkit`) or access to the repository checkout
- Virtual environment with project dependencies installed (`poetry install` or `poetry install`)
- Optional: Node.js toolchain if you plan to generate the NestJS framework

## Installation

### Using RapidKit CLI (recommended)

```bash
rapidkit modules add settings --profile fastapi/standard
rapidkit modules add settings --profile nestjs/standard
```

The CLI installs the module, synchronises vendor snapshots under
`.rapidkit/vendor/settings/<version>` and updates `.rapidkit/file-hashes.json` so future updates can
detect drift automatically.

### Manual installation via generator

```bash
.venv/bin/python src/modules/free/core/settings/generate.py fastapi ./sandbox/fastapi
.venv/bin/python src/modules/free/core/settings/generate.py nestjs ./sandbox/nestjs
```

The generator writes the same outputs as the CLI. Use this when developing locally or when running
smoke-tests in CI.

## Generated layout

| Path                                                       | Description                                         | Source template                                    |
| ---------------------------------------------------------- | --------------------------------------------------- | -------------------------------------------------- |
| `src/modules/free/essentials/settings/settings.py`         | `Settings` runtime facade with multi-source loading | `templates/variants/fastapi/settings.py.j2`        |
| `src/modules/free/essentials/settings/custom_sources.py`   | Vault/AWS Secrets/YAML bridge                       | `templates/variants/fastapi/custom_sources.py.j2`  |
| `src/modules/free/essentials/settings/hot_reload.py`       | File watcher for dev/staging                        | `templates/variants/fastapi/hot_reload.py.j2`      |
| `src/health/settings.py`                                   | FastAPI health endpoint + router helper             | `templates/base/settings_health.py.j2`             |
| `src/modules/free/essentials/settings/configuration.ts`    | NestJS configuration factory                        | `templates/variants/nestjs/configuration.ts.j2`    |
| `src/modules/free/essentials/settings/settings.service.ts` | NestJS injectable settings service                  | `templates/variants/nestjs/settings.service.ts.j2` |
| `src/health/settings.health.ts`                            | NestJS health controller                            | `templates/variants/nestjs/settings.health.ts.j2`  |
| `.rapidkit/vendor/settings/<version>`                      | Vendor snapshot for diff/rollback                   | `templates/base/*.j2`                              |

## Plugin Architecture

The settings module uses a plugin-based architecture to support multiple frameworks. Each framework
(FastAPI, NestJS, etc.) is implemented as a plugin that defines:

- Template mappings: Which templates to use for code generation
- Output paths: Where generated files should be placed
- Context enrichment: Framework-specific variables added to the template context
- Requirements validation: Checks for required tools (Python, Node.js, etc.)
- Post-generation hooks: Optional cleanup or processing after generation

### Available Frameworks

- **FastAPI**: Python web framework with dependency injection
- **NestJS**: Node.js/TypeScript framework with dependency injection

### Adding New Frameworks

To add support for a new framework:

1. Create a new plugin class inheriting from `FrameworkPlugin`
1. Implement the required abstract methods
1. Register the plugin in `frameworks/__init__.py`
1. Add corresponding templates in `templates/variants/<framework>/`

## Runtime quick start

```python
from src.modules.free.essentials.settings.settings import Settings


def bootstrap() -> None:
    settings = Settings()
    print(settings.ENV)
    print(settings.CONFIG_FILES)


if __name__ == "__main__":
    bootstrap()
```

The generated class automatically:

- loads `.env`, `.env.local`, `config.yaml` and extra sources defined in `custom_sources.py`
- applies overrides registered through `apply_module_overrides(..., "settings")`
- emits hot-reload events in environments listed in `HOT_RELOAD_ENV_ALLOWLIST`

## Working with overrides

1. Add your logic to `src/modules/free/essentials/settings/overrides.py`
1. Set the relevant environment variables to enable behaviour:
   - `RAPIDKIT_SETTINGS_EXTRA_DOTENV`
   - `RAPIDKIT_SETTINGS_RELAXED_ENVS`
   - `RAPIDKIT_SETTINGS_ALLOW_PLACEHOLDER_SECRET`
   - `RAPIDKIT_SETTINGS_LOG_REFRESH`
1. Import `Settings` anywhere in your application; hooks are registered automatically

For complex cases, consult `docs/advanced.md` to learn how to extend the generator context or plug
in telemetry.

## Validation and testing

### Developer regression tests

```bash
.venv/bin/python -m pytest tests/modules/settings -q
```

### End-user smoke test (per project)

1. Scaffold a temporary project or use a sample service directory.
1. Run the generator for the target framework.
1. Import `Settings` inside the service and call `Settings().refresh()`.
1. For FastAPI: register the generated dependency, call `register_settings_health(app)` and hit
   `/health/settings`.
1. For NestJS: ensure the config factory and `SettingsHealthController` resolve without throwing
   exceptions.

### Manual health checklist

- `python src/modules/free/core/settings/generate.py fastapi /tmp/out` succeeds
- Generated files compile
  (`python -m py_compile /tmp/out/src/modules/free/essentials/settings/settings.py`)
- `Settings().refresh()` logs structured output when `RAPIDKIT_SETTINGS_LOG_REFRESH=1`

These steps are also executed automatically by the health automation described below.

### Automation hooks

- Local commits run `settings-module-health` via pre-commit to smoke the generator and runtime
  wiring whenever settings sources or docs change.
- CI enforces the same script with `--strict-nestjs`, guaranteeing the NestJS smoke test runs on
  every pull request.
- Trigger the health script manually with `python scripts/check_module_integrity.py` (add `--help`
  for options) to debug failures or keep artifacts for inspection.
- Other modules can adopt the same pattern once they expose a deterministic generator script and
  smoke check; keep hooks module-specific to avoid slowing unrelated commits.

### Service health exposure

- FastAPI installations now ship `src/health/settings.py` with `register_settings_health(app)`;
  import the helper and call it during application bootstrap to expose `/health/settings` in your
  Swagger/OpenAPI surface.
- NestJS installations include a ready-to-use `SettingsHealthController`; register it inside your
  health module (or the primary application module) to expose the `GET /health/settings` route.
- The integrity script remains developer-facing; combine the generated endpoint with your own
  readiness checks to build a complete health surface for production.

### Downstream adoption checklist

After installing or upgrading the module, downstream teams should verify:

1. **Generator smoke:** run `rapidkit modules add settings --profile <framework>` or
   `python src/modules/free/core/settings/generate.py <framework> <target-dir>` in their
   environment.
1. **Runtime import:** compile a generated file
   (`python -m py_compile <target>/src/modules/free/essentials/settings/settings.py`) or instantiate
   `Settings()` in a small script.
1. **Service integration:** include an integration test that boots the FastAPI/NestJS service with
   the generated settings and confirms dependency injection resolves.
1. **Optional telemetry & hot reload:** when relying on these features, enable the relevant env
   variables and assert logs or events fire as expected.

## API reference

### Runtime APIs

| Symbol                                      | Description                                                 |
| ------------------------------------------- | ----------------------------------------------------------- |
| `Settings`                                  | Generated Pydantic settings class with multi-source loading |
| `Settings.refresh()`                        | Reload settings and optionally emit telemetry               |
| `custom_sources.load_additional_sources()`  | Bridge to Vault/AWS Secrets/YAML adapters                   |
| `apply_module_overrides(model, "settings")` | Registers override contracts                                |

### Generator APIs

| Symbol                         | Description                                              |
| ------------------------------ | -------------------------------------------------------- |
| `GeneratorError`               | Error type raised with actionable context and exit codes |
| `load_module_config()`         | Reads and validates `module.yaml`                        |
| `generate_vendor_files()`      | Materialises vendor snapshots                            |
| `generate_variant_files()`     | Renders framework-specific outputs using plugins         |
| `TemplateRenderer`             | Shared Jinja2 renderer with graceful fallback            |
| `ensure_version_consistency()` | Shared helper that bumps module versions automatically   |
| `get_plugin(framework)`        | Get a framework plugin instance                          |
| `list_available_plugins()`     | List all registered framework plugins                    |

### Plugin APIs

| Symbol                             | Description                                   |
| ---------------------------------- | --------------------------------------------- |
| `FrameworkPlugin`                  | Abstract base class for framework plugins     |
| `FastAPIPlugin`                    | FastAPI-specific plugin implementation        |
| `NestJSPlugin`                     | NestJS-specific plugin implementation         |
| `plugin.validate_requirements()`   | Check if framework dependencies are available |
| `plugin.get_template_mappings()`   | Get template-to-file mappings                 |
| `plugin.get_output_paths()`        | Get logical-name-to-output-path mappings      |
| `plugin.get_context_enrichments()` | Add framework-specific template variables     |

### CLI entry points

| Command                                             | Purpose                         |
| --------------------------------------------------- | ------------------------------- |
| `rapidkit modules add settings --profile <profile>` | Install module into a project   |
| `python generate.py <framework> <target-dir>`       | Run generator manually          |
| `pytest tests/modules/settings -q`                  | Execute module regression suite |

## Related documentation

- `docs/advanced.md`
- `docs/migration.md`
- `docs/troubleshooting.md`
- `src/modules/free/core/settings/README.md`
- `src/modules/free/core/settings/frameworks/` - Plugin architecture implementation
