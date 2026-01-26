# 📋 GitHub Templates Documentation

## 🎯 Overview

This document describes the GitHub templates used in the RapidKit project to standardize
contributions and maintain quality.

## 📁 Template Locations

All GitHub templates are located in the `.github/` directory as required by GitHub:

```text
.github/
├── PULL_REQUEST_TEMPLATE.md          # PR template
└── ISSUE_TEMPLATE/
    ├── bug_report.md                 # Bug report template
    └── feature_request.md            # Feature request template
```

## 🔧 Pull Request Template

**Location:** `.github/PULL_REQUEST_TEMPLATE.md`

### PR Template Purpose

Standardizes pull request format and ensures quality checks are performed.

### PR Template Sections

- **📋 Summary**: Description of changes and purpose
- **🔗 Related Issues**: Links to related GitHub issues
- **🏷️ Type of Change**: Categorization (bugfix, feature, docs, etc.)
- **✅ Checklist**: Quality assurance checklist

### PR Template Benefits

- Consistent PR format across all contributors
- Ensures testing and documentation requirements are met
- Improves review process efficiency

## 🐛 Bug Report Template

**Location:** `.github/ISSUE_TEMPLATE/bug_report.md`

### Bug Report Purpose

Standardizes bug reporting to ensure all necessary information is provided.

### Bug Report Sections

- Bug description
- Reproduction steps
- Expected vs actual behavior
- Environment details
- Error logs

### Bug Report Benefits

- Faster bug resolution with complete information
- Consistent bug tracking
- Better triage process

## ✨ Feature Request Template

**Location:** `.github/ISSUE_TEMPLATE/feature_request.md`

### Feature Request Purpose

Guides feature requests with structured information.

### Feature Request Sections

- Feature summary and problem it solves
- Use cases and workflows
- Proposed solution
- Alternative considerations

### Feature Request Benefits

- Well-thought-out feature proposals
- Clear requirements gathering
- Better prioritization decisions

## 🔒 Why These Stay in `.github/`

GitHub automatically recognizes and uses templates from the `.github/` directory:

1. **GitHub Standard**: This is the official location GitHub expects
1. **Automatic Integration**: Templates appear automatically in GitHub UI
1. **Functionality**: Moving them breaks GitHub's template system
1. **Best Practice**: Industry standard for open source projects

## 📖 Contributing Guidelines

For information on how to use these templates, see:

- [Contributing Guide](../contributing/CONTRIBUTING.md)
- [Development Workflow](../development/README.md)

## 🔄 Template Maintenance

Templates should be reviewed and updated periodically to:

- Reflect current project standards
- Include new quality checks
- Adapt to changing contribution patterns

______________________________________________________________________

_This documentation helps contributors understand the purpose and proper use of GitHub templates in
the RapidKit project._
