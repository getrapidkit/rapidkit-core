# Storage Module API Reference

## Classes

### FileStorage

Main service class for file operations.

#### Methods

##### `upload_file(filename: str, content: bytes, metadata: Dict | None = None) -> UploadResult`

Upload a file.

**Parameters:**

- `filename` (str): Name of the file
- `content` (bytes): File content
- `metadata` (Dict, optional): Additional metadata persisted alongside the file

**Returns:** `UploadResult` with file details

##### `download_file(file_id: str) -> bytes`

Download a file.

**Parameters:**

- `file_id` (str): ID of the file

**Returns:** File content as bytes. Raises `FileNotFoundError` if the file is missing.

##### `delete_file(file_id: str) -> bool`

Delete a file.

**Parameters:**

- `file_id` (str): ID of the file

**Returns:** True if deleted successfully

##### `get_file_info(file_id: str) -> FileMetadata`

Get file metadata.

**Parameters:**

- `file_id` (str): ID of the file

**Returns:** FileMetadata. Raises `FileNotFoundError` if the file is missing.

##### `health_check() -> Dict`

Check storage health.

**Returns:** Mapping with module status and adapter metrics

## Models

### FileMetadata

File metadata structure:

```python
class FileMetadata:
    file_id: str
    filename: str
    size: int
    mimetype: str | None
    checksum: str | None
    uploaded_at: datetime
    adapter: str
    extra: Dict[str, Any]
```

### UploadResult

Upload operation result:

```python
class UploadResult:
    success: bool
    file_id: str | None
    message: str | None
    metadata: FileMetadata | None
```

## Storage Adapters

### StorageAdapter (Abstract Base Class)

All adapters implement this interface:

- `save(file_id, payload, metadata=None) -> None`
- `load(file_id) -> bytes`
- `delete(file_id) -> None`
- `stat(file_id) -> FileMetadata`
- `health() -> Mapping`

### LocalStorageAdapter

Local filesystem storage.

### S3StorageAdapter (Scaffold)

AWS S3 adapter scaffold located under `templates/snippets/`. Provide a concrete implementation via
overrides.

### GCSStorageAdapter (Scaffold)

Google Cloud Storage adapter scaffold located under `templates/snippets/`. Provide a concrete
implementation via overrides.
