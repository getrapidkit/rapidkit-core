# 🚀 RapidKit Pull Request Template

## 📋 Summary

Provide a clear, concise description of the changes and their purpose.

**What changed:**

- \[Brief description of changes\]

**Why this change:**

- \[Explanation of the problem being solved or feature being added\]

## 🔗 Related Issues

- Closes: #\[issue_number\]
- Related: #\[issue_number\]
- See also: #\[issue_number\]

## 🏷️ Type of Change

Select all that apply:

- [ ] 🐛 **Bugfix** - Fixes a bug
- [ ] ✨ **Feature** - Adds new functionality
- [ ] 📚 **Documentation** - Updates documentation
- [ ] 🔧 **CI/CD** - Changes to build process or CI configuration
- [ ] 🏗️ **Architecture** - Changes to system architecture
- [ ] 🔒 **Security** - Security-related changes
- [ ] ⚡ **Performance** - Performance improvements
- [ ] 🧹 **Refactor** - Code refactoring (no functional changes)
- [ ] 🧪 **Testing** - Adding or updating tests
- [ ] 📦 **Dependencies** - Updates to dependencies

## ✅ Checklist

### Code Quality

- [ ] **Target Branch**: PR targets the correct branch (`main` for features, `develop` for ongoing
  work)
- [ ] **Tests**: Added/updated tests for new behavior
- [ ] **Linting**: All linting and type checks pass locally
- [ ] **Coverage**: Test coverage maintained or improved (no decrease on changed lines)
- [ ] **Documentation**: Code is well-documented with docstrings and comments

### Security & Compliance

- [ ] **Security Review**: No sensitive data or security vulnerabilities introduced
- [ ] **Signing**: Module signing requirements met (if applicable)
- [ ] **Dependencies**: No vulnerable or unapproved dependencies added
- [ ] **Secrets**: No secrets or private keys committed

### Documentation

- [ ] **README**: Updated if user-facing changes
- [ ] **Changelog**: Release notes updated for user-facing changes
- [ ] **API Docs**: API documentation updated for public API changes
- [ ] **Migration Guide**: Migration guide added for breaking changes

## 🧪 Testing

**Test Coverage:**

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] E2E tests added/updated (if applicable)

**Test Results:**

```bash
# Run tests locally
pytest tests/ -v --cov=src/

# Run linting
ruff check src/
mypy src/
```

## 🚀 Deployment Notes

**Breaking Changes:** \[Yes/No\]

- \[List any breaking changes and migration steps\]

**Database Changes:** \[Yes/No\]

- \[Describe any database schema changes\]

**Environment Variables:** \[Yes/No\]

- \[List any new or changed environment variables\]

## 🔍 Additional Context

Add any other context about the PR here:

- Screenshots (if UI changes)
- Performance benchmarks (if performance changes)
- Security implications (if security-related)
- Future considerations

______________________________________________________________________

**By submitting this PR, I confirm that:**

- [ ] My changes follow the project's coding standards
- [ ] I have tested my changes thoroughly
- [ ] I have updated documentation as needed
- [ ] This PR is ready for review

______________________________________________________________________

_This template helps maintain consistency and quality across RapidKit's development process._
