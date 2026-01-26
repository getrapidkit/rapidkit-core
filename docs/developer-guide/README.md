# 🛠️ RapidKit Community Developer Guide

Welcome to the RapidKit Community developer documentation. This guide explains how to contribute to
the open-source distribution, build high-quality modules, and keep your local environment aligned
with the published toolchain. Everything here assumes you are working inside the community
repository — the same one that ships to every open-source user.

______________________________________________________________________

## 🎯 What You’ll Learn

- Setting up a local development environment for RapidKit Community
- Understanding the repository layout and where to make changes
- Following contribution standards (testing, linting, commit style)
- Building, documenting, and publishing community modules
- Managing the module lock file and keeping releases reliable

______________________________________________________________________

## 🚀 Before You Start

| Requirement | Recommended Version | Notes                                           |
| ----------- | ------------------- | ----------------------------------------------- |
| Python      | 3.10.14             | Use `pyenv`, `asdf`, or your OS package manager |
| Poetry      | Latest stable       | Handles dependency management                   |
| Git         | 2.40+               | Required for contributions                      |
| Docker      | Latest stable       | Optional, but useful for smoke tests            |

Clone the community repository and install dependencies:

```bash
git clone https://github.com/getrapidkit/community.git rapidkit-community
cd rapidkit-community

# Create and activate a virtual environment if you prefer
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install project dependencies
poetry install

# Install git hooks (optional but recommended)
poetry run pre-commit install
poetry run pre-commit install --hook-type commit-msg
```

> 💡 Tip: This repository powers all downstream distributions. Ship improvements here first so every
> community user receives them automatically.

______________________________________________________________________

## 🔁 Updating Templates After Customisation

The lean module layout is designed so template refreshes remain safe and predictable:

1. Inspect the current state with `rapidkit diff module <name>`.
1. Apply compatible changes and regenerate snapshots with `rapidkit merge module <name>`.
1. Resolve any `locally_modified` or `diverged` files manually, then rerun the merge to refresh the
   registry hash.

See **[Module System](../modules/overview.md)** for an in-depth breakdown of the lean structure and
**[Override Contracts](override-contracts.md)** for the supported customisation points.

> ℹ️ Every module must keep `config/snippets.yaml` and `templates/snippets/` so reusable snippets
> are tracked across generated outputs.

> ℹ️ Spec v2 ignores internal state files such as `.module_state.json` and
> `.module_pending_changelog.yaml` during structure validation, so you can commit them without
> triggering a compliance error.

______________________________________________________________________

## 🧪 Testing and CI Guidelines

- Run Python tests with `poetry run pytest` and ensure the settings module covers
  `tests/modules/settings` at a minimum.
- Use `scripts/check_module_integrity.py` for NestJS smoke coverage (the same script CI executes).
- Whenever you add new tests, register them under the `testing` section of `module.yaml`.

For extended examples (E2E, performance, security), explore the `tests/` tree and the
**[Testing Guide](../testing/README.md)**.

______________________________________________________________________

## 🚀 Release Workflow

### Version Management

```bash
# Update version
poetry version patch  # or minor, major

# Update changelog
# Edit CHANGELOG.md with new features and fixes

# Create release commit
git add .
git commit -m "chore: release v1.2.3"

# Create git tag
git tag -a v1.2.3 -m "Release v1.2.3"

# Push changes and tags
git push origin main
git push origin v1.2.3
```

### Automated Release

```yaml
# .github/workflows/release.yml
name: Release
on:
    push:
        tags:
            - "v*"

jobs:
    release:
        runs-on: ubuntu-latest
        steps:
            - uses: actions/checkout@v3
            - name: Publish to PyPI
              run: |
                  poetry build
                  poetry publish --username ${{ secrets.PYPI_USERNAME }} --password ${{ secrets.PYPI_PASSWORD }}
```

## 📚 Further Reading

- **[Override Contracts](override-contracts.md)** – Safe customisation techniques for modules
- **[Module Standards](module-standards.md)** – Enforcing the structure contract and validator tools
- **[Module System](../modules/overview.md)** – Lean layout and module requirements
- **[Template Engine](../api-reference/templates.md)** – Template engine internals
- **[CLI JSON Schemas](../architecture/CLI_JSON_SCHEMAS.md)** – CLI schema reference
- **[Testing Guide](../testing/README.md)** – Testing policies and coverage tooling
- **[GitHub Actions Overview](github-actions-overview.md)** – How CI, distribution, and release
  workflows connect

## 🤝 Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and community support
- **Discord**: Real-time chat for contributors
- **Newsletter**: Monthly updates and roadmap

### Recognition

Contributors are recognized through:

- **GitHub Contributors** list
- **CHANGELOG.md** entries
- **Release notes** mentions
- **Community badges**

______________________________________________________________________

**🚀 Ready to contribute to RapidKit? Your ideas and code can make a difference!**
