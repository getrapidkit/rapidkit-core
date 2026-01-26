# Kit Consumer Guide

This guide distils the recommended workflow for teams that scaffold applications from the official
RapidKit kits (for example `fastapi.standard`). It assumes the RapidKit CLI is installed inside your
virtual environment.

## 1. Scaffold the project

Run the `create project` command with the desired kit slug and project name. Provide the output
folder to keep generated assets isolated from your mono-repo.

```bash
poetry run rapidkit create project fastapi.standard demo_app \
  --output ./tmp/kit_demo \
  --install-essentials \
  --variable enable_ci=true
```

- `--install-essentials` asks the CLI to install the default module set (settings, logging, etc.).
- Pass additional `--variable key=value` pairs to feed kit-specific switches such as `auth_strategy`
  or `enable_postgres` (inspect the kit `generator.py` for the accepted keys).

If a module installation fails (for example `free/logging`), rerun `rapidkit add module logging`
inside the generated project after fixing the root cause (usually missing `module.yaml` metadata or
network issues). The scaffolder prints the failing module name to simplify follow-up actions.

## 2. Verify module integrity

From the new project directory run:

```bash
rapidkit modules status
rapidkit modules lock --overwrite
```

The status command reports files that deviate from the vendor snapshot. The lock command refreshes
`.rapidkit/vendor/**` so the whole team reproduces identical artefacts.

To lint the generated structure against the canonical specification execute:

```bash
poetry run python -c "from core.services.module_structure_validator import ensure_module_structure; ensure_module_structure('free/essentials/deployment')"
```

Swap the slug with any module you install (for example `free/essentials/settings`).

## 3. Run smoke tests

Each kit ships with a minimal test matrix. Execute the recommended checks before committing:

```bash
poetry run pytest
poetry run mypy src
```

Extend the suite with module-specific tests (for instance `tests/modules/deployment`) when the
application customises overrides or snippets.

## 4. Customise safely

1. Prefer editing `module.yaml` options (for example `options.include_ci`) instead of forking
   templates.
1. Use the module override stubs (`overrides.py`) to inject behaviour without touching vendor files.
1. Append features via the snippet registry—add snippets under `templates/snippets/` and register
   them in `config/snippets.yaml`.

After every change re-run the generator:

```bash
poetry run python -m src.modules.free.essentials.deployment.generate fastapi .
```

Finally, commit both project artefacts and the `.rapidkit/vendor/**` snapshot to keep downstream
pipelines deterministic.
