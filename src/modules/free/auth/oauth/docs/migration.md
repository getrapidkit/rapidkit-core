# OAuth Module Migration Guide

The OAuth module has not yet introduced breaking changes. When a new release ships, follow the
standard upgrade process:

1. Regenerate the module into a temporary directory and review the diff.
1. Copy over template updates you want to adopt; keep custom code in your project specific files.
1. Rerun the test suite under `tests/modules/free_auth_oauth` to validate provider integrations.

Future releases will record detailed steps here.
