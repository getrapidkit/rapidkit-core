# Passwordless Module Migration Guide

The module is currently in its first stable iteration. When future releases introduce behavioural
changes, steps will be documented here. Until then follow the general RapidKit module upgrade flow:

1. Regenerate the module into a temporary directory.
1. Review and merge template updates that improve your use case.
1. Run `poetry run pytest tests/modules/free_auth_passwordless -q` to confirm behaviour.
