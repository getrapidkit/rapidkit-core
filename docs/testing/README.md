# 🧪 Test Organization Structure

## 📁 Directory Structure

```text
tests/
├── cli/                    # CLI command tests
│   ├── commands/          # Individual command tests
│   ├── lifecycle/         # CLI lifecycle tests
│   └── coverage/          # CLI coverage tests
├── core/                  # Community engine tests
│   ├── engine/           # Engine component tests
│   ├── services/         # Service layer tests
│   └── config/           # Configuration tests
├── kits/                  # Kit-specific tests
│   ├── fastapi/          # FastAPI kit tests
│   └── generators/       # Generator tests
├── modules/               # Module-related tests
│   ├── signing/          # Module signing tests
│   └── management/       # Module management tests
├── services/              # Service integration tests
│   ├── dependency/       # Dependency management tests
│   ├── snippet/          # Snippet injection tests
│   └── telemetry/        # Telemetry tests
└── utils/                 # Utility tests
    ├── license/          # License-related tests
  ├── validation/       # Validation tests
  └── helpers/          # Helper function tests
```

## 🎯 Test Categories

### CLI Tests (`tests/cli/`)

- Command functionality
- CLI lifecycle
- User interactions
- Help system

### Community Tests (`tests/core/`)

- Engine components
- Business logic
- Configuration management
- Community utilities

### Kit Tests (`tests/kits/`)

- Framework-specific generators
- Kit configurations
- Template rendering

### Module Tests (`tests/modules/`)

- Module signing
- Module validation
- Module management

### Service Tests (`tests/services/`)

- External integrations
- Dependency management
- Snippet injection
- Telemetry

### Utility Tests (`tests/utils/`)

- Helper functions
- Validation logic
- License management

## 🚀 Running Tests

```bash
# Run all tests
pytest

# Run specific category
pytest tests/cli/
pytest tests/core/
pytest tests/kits/

# Run with the enforced coverage gate (70%)
pytest --cov=src --cov-report=term --cov-report=html --cov-fail-under=70
```

### Module QA shortcut

```bash
# Validate module structure + parity
make module-qa

# Equivalent tox environment (used in CI)
tox -e modules
```

## 🏗️ Enterprise Local Matrix (tox)

To mirror the GitHub Actions matrix without burning CI minutes, use the bundled `tox` workflow:

```bash
# Install tox once
python -m pip install --upgrade "tox>=4.10"

# Run the CI-equivalent unit tests
tox -e unit-ubuntu310
tox -e unit-windows310
tox -e unit-macos310

# Optional legacy Windows cp1252 smoke
tox -e legacy-windows310

# Run linters / formatters and type-checking with one command
tox -e lint,typecheck

# Full matrix (serial, matches the new pre-push hook)
tox
```

### What each environment covers

- **`unit-ubuntu310`** – ubuntu-latest job w/ Python 3.10 + coverage gates.
- **`unit-windows310`** – mirrors the GitHub Actions Windows job (UTF-8 console).
- **`unit-macos310`** – macOS 13/14 equivalent smoke run.
- **`legacy-windows310`** – cp1252 console simulation targeting the generators/docs suite.
- **`lint` / `typecheck`** – wraps `ruff`, `black --check`, and `mypy` with the same arguments as
  CI.

> 💡 Tip: need to force a specific interpreter path? export `TOX_PY310=/abs/path/to/python3.10`
> before running tox. The pre-push hook will automatically run the entire matrix via
> `poetry run tox -e unit-ubuntu310,...` so you learn about cross-platform failures before GitHub
> Actions does.

## 📊 Coverage Gates

- **Hard CI gate**: `pyproject.toml` sets `fail_under = 70`, so every `pytest --cov` run must hit at
  least 70%.
- **Core Engine**: Keep ≥70% to avoid being the limiting factor for the gate.
- **CLI Commands**: Target ≥75% because command regressions surface at runtime.
- **Critical Services (modules, dependency, snippet)**: Target ≥80% to protect contract shims.
- **New features**: land with regression tests covering success + failure paths to avoid sudden
  drops below 70%.

## 🛠️ Test Naming Convention

- `test_{component}_{functionality}.py`
- `test_{feature}_{scenario}.py`
- Use descriptive names that explain what is being tested

## ✅ Best Practices

1. **One concept per test**: Each test should verify one specific behavior
1. **Descriptive names**: Test names should clearly indicate what they verify
1. **Arrange-Act-Assert**: Follow this pattern for all tests
1. **Independent tests**: Tests should not depend on each other
1. **Fast execution**: Keep tests fast to encourage frequent running
1. **Modules stay green**: run `make module-qa` (or `tox -e modules`) before proposing module
   changes
