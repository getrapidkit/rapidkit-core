# Advanced Topics

Capture extensibility hooks, override patterns, and performance considerations.

## Overrides

Use `overrides.py` to supply environment-driven defaults and to copy an additional snippet file into
the generated project.

- `RAPIDKIT_API_KEYS_*` environment variables mutate generation-time defaults.
- `RAPIDKIT_API_KEYS_EXTRA_SNIPPET*` supports copying an additional file for project-specific glue.
