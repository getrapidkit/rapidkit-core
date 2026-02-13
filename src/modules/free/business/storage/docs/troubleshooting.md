# Troubleshooting

## Common Issues

### Upload Fails with "File Size Exceeds Limit"

**Solution**:

- Increase `max_file_size` in `config/storage.yaml` or split large files.

### S3 Upload Times Out

**Solution**:

- Check AWS credentials
- Verify bucket name and region
- Increase timeout in configuration
- Confirm your custom S3 adapter override is deployed and matches the latest scaffold

### Health Check Returns "Unhealthy"

**Solution**:

- Check storage adapter connectivity
- Verify disk space (local storage)
- Check cloud service status (S3/GCS)

### File Not Found After Upload

**Solution**:

- Verify file_id is correct
- Check adapter configuration
- Ensure file wasn't deleted

## Debugging

Enable debug logging:

```yaml
logging:
  level: DEBUG
```

View detailed error messages:

```python
result = await storage.upload_file(filename, content)
if not result.success:
    print(result.message)  # Detailed error info
```

## Performance Issues

- Check file size limits
- Monitor concurrent operations
- Review adapter performance
- Profile with storage metrics

## Getting Help

- [GitHub Issues](https://github.com/getrapidkit/rapidkit-core/issues)
- [Discussions](https://github.com/getrapidkit/rapidkit-core/discussions)
- [Documentation](https://docs.rapidkit.top)
