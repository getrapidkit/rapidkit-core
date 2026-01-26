# Advanced Storage Topics

## Custom Adapters

Create custom storage adapters by inheriting from `StorageAdapter`:

```python
from typing import Any, Dict, Mapping
from modules.free.business.storage.types.storage import FileMetadata, StorageAdapter


class CustomAdapter(StorageAdapter):
    async def save(
        self,
        file_id: str,
        payload: bytes,
        *,
        metadata: Mapping[str, Any] | None = None,
    ) -> None: ...

    async def load(self, file_id: str) -> bytes: ...

    async def delete(self, file_id: str) -> None: ...

    async def stat(self, file_id: str) -> FileMetadata: ...

    async def health(self) -> Mapping[str, Any]: ...
```

## Image Processing

The module includes image optimization:

```yaml
# Enable image processing in config
storage:
  image_processing:
    enabled: true
    thumbnails:
      small: {width: 150, height: 150}
      medium: {width: 300, height: 300}
```

## Health Checks

Comprehensive health monitoring:

```python
health = await storage.health_check()

print(f"Status: {health['status']}")
print(f"Available space: {health['available_space']}")
```

## Security

- **File Validation**: Automatic file type and size checks
- **Scanning**: Optional virus/malware scanning
- **Access Control**: Integration with authentication modules
- **Encryption**: Support for encrypted storage

## Performance Tuning

- Adjust `chunk_size` for streaming large files
- Enable `enable_caching` for frequently accessed files
- Configure `thread_pool_size` for concurrent operations

## Monitoring

Monitor storage metrics:

- Upload/download rates
- Error rates
- Storage utilization
- Adapter performance
