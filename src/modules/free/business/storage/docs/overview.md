# File Storage & Media Management Module

## Overview

The Storage module provides a unified, production-ready interface for handling file uploads,
storage, and media management across multiple backends (local filesystem, S3, Google Cloud Storage).

## Features

- **Multi-Adapter Support**: Local adapter is production-ready. S3 and GCS adapters ship as
  scaffolds and require custom overrides before deployment.
- **Async-First Design**: Full async/await support for FastAPI and NestJS
- **Image Processing**: Built-in thumbnail generation and optimization
- **Health Checks**: Comprehensive health monitoring and diagnostics
- **Framework Agnostic**: Works with FastAPI and NestJS out of the box
- **Secure by Default**: File validation, scanning, and access control

## Quick Start

### FastAPI

```python
from fastapi import FastAPI, UploadFile
from src.modules.free.business.storage.storage import FileStorage

app = FastAPI()
storage = FileStorage()


@app.post("/upload")
async def upload(file: UploadFile):
    return await storage.upload_file(file.filename, await file.read())
```

### NestJS

```typescript
import { Injectable } from '@nestjs/common';
import { FileStorage } from './storage.service';

@Injectable()
export class AppService {
  constructor(private storage: FileStorage) {}

  async uploadFile(file: Express.Multer.File) {
    return await this.storage.uploadFile(file);
  }
}
```

## Supported Adapters

- **Local**: Filesystem-based storage
- **S3**: Amazon S3 compatible storage
- **GCS**: Google Cloud Storage

## Next Steps

- [Usage Guide](./usage.md) - Detailed usage examples
- [API Reference](./api-reference.md) - Complete API documentation
- [Configuration](./usage.md#configuration) - Configuration options
- [Advanced Guide](./advanced.md) - Advanced topics

## Security considerations

This module may touch sensitive data or privileged actions depending on how it is configured.

- Security: document configuration boundaries and expected trust assumptions.
- Threat model: consider abuse cases (rate limiting, replay, injection) relevant to your
  environment.

If you operate in a regulated environment, include a brief audit trail strategy (what you log,
retention, who can access).
