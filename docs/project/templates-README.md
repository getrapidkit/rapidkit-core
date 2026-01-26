# RapidKit Templates

This directory contains templates that can be used in other repositories to set up RapidKit
automation.

## 🎯 Real-World Example for Community Users

Imagine you're building a FastAPI app with RapidKit modules:

### Before (Manual Process)

```bash
# Developer makes changes to auth module
vim src/modules/auth/module.yaml

# Forgets to update lock file
git add .
git commit -m "Update auth module"

# Later, CI fails because lock file is outdated
# Developer has to manually fix it
rapidkit modules lock --overwrite
```

### After (Automated Process)

```bash
# Developer makes changes to auth module
vim src/modules/auth/module.yaml

# Pre-commit automatically updates lock file
git add .
git commit -m "Update auth module"

# CI passes because lock file is always current ✅
```

## 🔒 Security & Safety

**This automation is completely safe for all users:**

### What it does:

- ✅ **Only reads** module configuration files
- ✅ **Only writes** to `.rapidkit/modules.lock.yaml`
- ✅ **No network access** or external communications
- ✅ **No privilege escalation**
- ✅ **No sensitive data exposure**

### What it doesn't do:

- ❌ **No code execution** beyond RapidKit CLI
- ❌ **No file system access** outside project directory
- ❌ **No database modifications**
- ❌ **No external API calls**
- ❌ **No security policy changes**

### Risk Assessment: **ZERO RISK** 🛡️

This is equivalent to running `rapidkit modules lock --overwrite` manually - just automated!

## 💡 Practical Benefits

### For Individual Developers

- **Never forget** to update lock files
- **Consistent** module versions across team
- **Faster development** cycle
- **Fewer CI failures** due to outdated locks

### For Teams

- **Standardized workflow** across all repositories
- **Automated compliance** with module versioning
- **Reduced manual work** for maintainers
- **Better collaboration** with consistent lock files

### For Organizations

- **Governance** through automated versioning
- **Audit trail** of module changes
- **Consistency** across all projects
- **Reduced support** tickets about lock file issues

## Available Templates

### 1. Pre-commit Template

**File:** `rapidkit-pre-commit-template.yml`

Use this template to add modules lock automation to your pre-commit configuration.

```bash
# Copy to your repository
cp rapidkit-pre-commit-template.yml .pre-commit-config.yaml

# Or merge with existing config
cat rapidkit-pre-commit-template.yml >> .pre-commit-config.yaml
```

### 2. GitHub Actions Template

**File:** `rapidkit-github-actions-template.yml`

Use this template to set up automatic modules lock updates via GitHub Actions.

```bash
# Copy to your repository
mkdir -p .github/workflows
cp rapidkit-github-actions-template.yml .github/workflows/auto-update-modules-lock.yml
```

## 🚀 Quick Start for Community Users

### Step 1: Copy Templates (2 minutes)

```bash
# Copy pre-commit template
curl -s https://raw.githubusercontent.com/getrapidkit/core/main/docs/project/rapidkit-pre-commit-template.yml >> .pre-commit-config.yaml

# Copy GitHub Actions template
mkdir -p .github/workflows
curl -s https://raw.githubusercontent.com/getrapidkit/core/main/docs/project/rapidkit-github-actions-template.yml > .github/workflows/auto-update-modules-lock.yml
```

### Step 2: Install Pre-commit (1 minute)

```bash
# Install pre-commit if not already installed
pip install pre-commit

# Setup hooks in your repository
pre-commit install
```

### Step 3: Test It (30 seconds)

```bash
# Make a change to any module
echo "# Test change" >> src/modules/auth/README.md

# Commit - lock file updates automatically!
git add .
git commit -m "Test module change"
```

### Step 4: Enjoy Automation! 🎉

From now on, every time you change modules, the lock file updates automatically.

## Usage Instructions

1. **Choose the template(s)** you need based on your repository setup
1. **Copy the template** to the appropriate location in your repository
1. **Customize** the configuration if needed (branches, paths, etc.)
1. **Test** the automation by making changes to modules and committing

## Requirements

- **RapidKit CLI** must be installed in your repository
- **Python 3.10.14** for running the CLI
- **Pre-commit** (if using the pre-commit template)
- **GitHub Actions** (if using the GitHub Actions template)

## Support

For questions about these templates, check the main developer guide:

- `docs/developer-guide/README.md` - Modules Lock Management section

______________________________________________________________________

## 📝 Summary

**What is this?** 🤔

- Automatic updater for RapidKit module lock files
- Prevents "forgot to update lock file" problems
- Works locally (pre-commit) and in CI (GitHub Actions)

**Who needs it?** 👥

- Anyone using RapidKit with modules
- Individual developers, teams, organizations
- Community, Pro, and Enterprise users

**Why use it?** 💪

- Zero manual work
- Consistent module versions
- Fewer CI failures
- Better team collaboration

**Is it safe?** 🛡️

- 100% safe - only updates lock files
- No security risks
- No external communications
- Equivalent to running CLI manually

**Ready to try?** 🚀 Copy the templates above and start automating today!

______________________________________________________________________

_This automation makes RapidKit development smoother for everyone!_ 🎯
