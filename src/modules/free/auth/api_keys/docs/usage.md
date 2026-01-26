# Usage

End-to-end setup and integration notes for the Api Keys module.

## Quickstart

1. Install the module:

```bash
rapidkit add module api_keys
rapidkit modules lock --overwrite
```

2. Review defaults in `config/api_keys.yaml` and set a hashing pepper via the environment. The
   runtime requires a pepper to derive and verify token digests.

1. Wire the FastAPI router:

```python
from fastapi import FastAPI

from src.modules.free.auth.api_keys.api_keys import build_router

app = FastAPI()
app.include_router(build_router(prefix="/api_keys"))
```

4. Verify health during local development:

```bash
curl -s http://localhost:8000/api_keys/health | python -m json.tool
```

## Demo

This module includes a small demo harness under `scripts/run_demo.py`.

```bash
python scripts/run_demo.py
```
