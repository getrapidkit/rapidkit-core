# Session Module Migration Guide

Keep an eye on the changelog for breaking changes. Until additional releases ship, follow these
steps when updating:

1. Regenerate the module and review the diff for runtime or template improvements.
1. Propagate signing key updates across all environments before deploying.
1. Run `poetry run pytest tests/modules/free_auth_session -q` to confirm behaviour.
