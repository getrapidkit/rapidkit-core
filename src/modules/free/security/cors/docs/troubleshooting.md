# CORS Troubleshooting Guide

This guide helps you resolve common CORS-related issues in your FastAPI applications.

## Common Issues

### 1. CORS Error in Browser

**Error**: `Access to XMLHttpRequest at '...' from origin '...' has been blocked by CORS policy`

**Solutions**:

#### Check Origin Configuration

Ensure your frontend domain is in `allow_origins`:

```python
# ✅ Add your frontend domain
cors_config = CORSConfig(allow_origins=["http://localhost:3000", "https://myapp.com"])

# ❌ Don't use wildcard with credentials
cors_config = CORSConfig(allow_origins=["*"], allow_credentials=True)  # This won't work
```

#### Verify HTTPS in Production

Always use HTTPS origins in production:

```python
# ✅ Production-ready
cors_config = CORSConfig(allow_origins=["https://myapp.com", "https://app.myapp.com"])
```

### 2. Preflight Request Failures

**Error**: `OPTIONS` requests failing with CORS errors

**Solutions**:

#### Allow OPTIONS Method

Ensure `OPTIONS` is in allowed methods:

```python
cors_config = CORSConfig(allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
```

#### Check Headers

Allow necessary headers:

```python
cors_config = CORSConfig(
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"]
)
```

### 3. Credentials Not Working

**Error**: Cookies/auth headers not sent with requests

**Solutions**:

#### Enable Credentials

Set `allow_credentials=True` and specify explicit origins:

```python
cors_config = CORSConfig(
    allow_origins=["https://myapp.com"],  # Explicit domain required
    allow_credentials=True,
    allow_headers=["Authorization", "Content-Type"],
)
```

#### Check Frontend Configuration

Ensure your frontend includes credentials:

```javascript
// Axios example
axios.defaults.withCredentials = true;

// Fetch API example
fetch('/api/data', {
  method: 'GET',
  credentials: 'include'
});
```

### 4. Mobile App Issues

**Error**: CORS issues with mobile apps or native clients

**Solution**: Mobile apps typically don't need CORS. The issue might be:

- Wrong API endpoint URL
- Missing protocol (http vs https)
- Firewall or network restrictions

### 5. Development vs Production Differences

**Common Issue**: Works in development but fails in production

**Check**:

- Development uses `http://localhost:3000`, production uses `https://myapp.com`
- Environment variables not set correctly
- Different CORS configurations per environment

```python
# Use environment-specific configuration
import os

cors_config = CORSConfig(
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
)
```

## Debugging Steps

### 1. Check Browser Network Tab

1. Open browser DevTools → Network tab
1. Make the failing request
1. Look for OPTIONS preflight request
1. Check response headers for CORS headers

### 2. Verify Server Logs

Check FastAPI logs for CORS middleware activity:

```python
# Enable debug logging
import logging

logging.basicConfig(level=logging.DEBUG)
```

### 3. Test with curl

Test CORS headers directly:

```bash
# Test preflight request
curl -X OPTIONS -H "Origin: https://myapp.com" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Authorization" \
     -v https://api.myapp.com/endpoint

# Check for these response headers:
# Access-Control-Allow-Origin: https://myapp.com
# Access-Control-Allow-Credentials: true
# Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
# Access-Control-Allow-Headers: Authorization, Content-Type
```

### 4. Use Browser Extensions

- **CORS Unblock**: Temporarily disable CORS for testing (not for production)
- **ModHeader**: Manually add CORS headers for testing

## Configuration Validation

### Test Your Configuration

Create a test to validate your CORS setup:

```python
from src.modules.free.security.cors.cors import CORSConfig, create_cors_middleware


def test_cors_configuration():
    config = CORSConfig(
        allow_origins=["https://myapp.com"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    middleware = create_cors_middleware(config)

    # Validate configuration
    assert "https://myapp.com" in middleware.allow_origins
    assert middleware.allow_credentials is True
    assert "OPTIONS" in middleware.allow_methods
    assert "Authorization" in middleware.allow_headers
```

### Common Configuration Mistakes

```python
# ❌ Wrong: Wildcard with credentials
CORSConfig(allow_origins=["*"], allow_credentials=True)

# ❌ Wrong: Missing OPTIONS method
CORSConfig(allow_methods=["GET", "POST", "PUT", "DELETE"])

# ❌ Wrong: Case-sensitive headers
CORSConfig(allow_headers=["authorization"])  # Should be "Authorization"

# ✅ Correct
CORSConfig(
    allow_origins=["https://myapp.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
```

## Performance Considerations

### Pre flight Caching

Set appropriate `max_age` to cache preflight requests:

```python
# Cache preflight for 1 hour
cors_config = CORSConfig(max_age=3600)

# Cache preflight for 24 hours
cors_config = CORSConfig(max_age=86400)
```

### Minimize Allowed Origins

Use specific origins instead of wildcards for better performance and security:

```python
# ✅ Specific origins (better performance)
cors_config = CORSConfig(
    allow_origins=["https://app.myapp.com", "https://admin.myapp.com"]
)

# ❌ Wildcard (worse performance, less secure)
cors_config = CORSConfig(allow_origins=["*"])
```

## Advanced Issues

### Multiple Origins with Regex

If you need pattern matching for origins, use a custom middleware:

```python
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
import re


class RegexCORSMiddleware(CORSMiddleware):
    def __init__(self, *args, **kwargs):
        self.origin_patterns = kwargs.pop("origin_patterns", [])
        super().__init__(*args, **kwargs)

    def is_allowed_origin(self, origin: str) -> bool:
        # Check exact matches first
        if origin in self.allow_origins:
            return True

        # Check regex patterns
        for pattern in self.origin_patterns:
            if re.match(pattern, origin):
                return True

        return False


# Usage
app.add_middleware(
    RegexCORSMiddleware,
    allow_origins=[],  # Disable default checking
    origin_patterns=[r"https://.*\.myapp\.com$"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Custom Headers

For custom headers, ensure they're properly allowed:

```python
cors_config = CORSConfig(
    allow_headers=["X-Custom-Header", "X-API-Version"],
    expose_headers=["X-Rate-Limit", "X-Request-ID"],
)
```

## Getting Help

If you're still having issues:

1. Check the [CORS specification](https://fetch.spec.whatwg.org/#cors-protocol)
1. Review FastAPI's [CORS documentation](https://fastapi.tiangolo.com/tutorial/cors/)
1. Test with a minimal CORS configuration first
1. Use the integration tests provided by the module

## Related Documentation

- [Usage Guide](usage.md) - Basic setup and configuration
- [Advanced Guide](advanced.md) - Complex scenarios and customization
- [Migration Guide](migration.md) - Upgrading from other CORS solutions
