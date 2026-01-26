"""File Storage & Media Management Module.

Production-ready file storage with support for local, S3, and GCS adapters.

Example:
    ```python
    from modules.free.business.storage import FileStorage

    storage = FileStorage()
    result = await storage.upload_file("document.pdf", file_bytes)
    ```
"""

from __future__ import annotations

__version__ = "1.0.0"
__all__ = [
    "FileStorage",
    "StorageAdapter",
    "LocalStorageAdapter",
    "FileMetadata",
    "UploadResult",
]

# Public API exports would go here
# from .storage import FileStorage, StorageAdapter, LocalStorageAdapter
# from .models import FileMetadata, UploadResult
