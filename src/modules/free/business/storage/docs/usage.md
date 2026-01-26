# Storage Module Usage Guide

## Installation

The module is automatically scaffolded with your project. Configuration is in `config/storage.yaml`.

## Basic Usage

### Upload a File

```python
from src.modules.free.business.storage.storage import FileStorage

storage = FileStorage()

# Upload a file
result = await storage.upload_file(
    filename="document.pdf",
    content=file_bytes,
    metadata={"type": "document", "user": "john"},
)

print(f"File uploaded: {result.file_id}")
```

### Download a File

```python
# Download file content
content = await storage.download_file(file_id)

if content:
    with open("downloaded.pdf", "wb") as f:
        f.write(content)
```

### Delete a File

```python
# Delete file
success = await storage.delete_file(file_id)
```

### Get File Information

```python
# Get file metadata
metadata = await storage.get_file_info(file_id)

print(f"Filename: {metadata.filename}")
print(f"Size: {metadata.size} bytes")
print(f"Type: {metadata.mimetype}")
```

## Configuration

Configure storage settings in `config/storage.yaml`:

```yaml
storage:
    adapter: local  # S3/GCS require custom overrides in v1.0

    local:
        base_path: "./storage/uploads"
        max_file_size: 104857600  # 100MB

    s3:
        enabled: false  # flip to true after providing a working override implementation
        bucket: "my-bucket"
        region: "us-east-1"
```

## Error Handling

```python
result = await storage.upload_file("file.txt", content)

if not result.success:
    print(f"Upload failed: {result.message}")
else:
    print(f"File ID: {result.file_id}")
```

## Best Practices

1. **Always validate files** before upload
1. **Use appropriate adapters** for your infrastructure
1. **Keep S3/GCS overrides in sync** with upstream templates when upgrading
1. **Monitor health checks** regularly
1. **Set file size limits** appropriately
1. **Implement proper access control**
