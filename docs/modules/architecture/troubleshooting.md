# RapidKit Modular System - Troubleshooting Guide

## Common Issues and Solutions

### Module Installation Issues

#### Module Not Found

**Symptoms:**

- `rapidkit add module <module>` fails with "module not found"
- CLI shows available modules but your module isn't listed

**Solutions:**

1. Check module name spelling and case sensitivity
1. Verify the module is present in the tier catalog `src/modules/<tier>/modules.yaml` and is not
   gated as unavailable (for example status planned)
1. Check if module is in correct category
1. Use `rapidkit modules list` / `rapidkit modules search <query>` to confirm the CLI can see it

#### Dependency Conflicts

**Symptoms:**

- Installation fails with dependency errors
- "Conflicting modules" error message

**Solutions:**

1. Review module dependencies in `module.yaml` (`depends_on`)
1. Check for conflicting modules
1. Re-run with `rapidkit add module <slug> --with-deps` to let the installer converge prerequisites
1. Remove conflicting modules before installation
1. Use `--force` flag only as last resort

#### Permission Errors

**Symptoms:**

- "Permission denied" during installation
- Cannot write to module directories

**Solutions:**

1. Check file system permissions
1. Run CLI with appropriate user privileges
1. Verify RapidKit installation directory permissions
1. Check if modules directory is writable

### Configuration Issues

#### Configuration Not Loading

**Symptoms:**

- Application fails to start
- Configuration values missing or incorrect
- Hot reload not working

**Solutions:**

1. Validate configuration file syntax (YAML/JSON/TOML)
1. Check file paths in configuration sources
1. Verify environment variable names match prefix
1. Test configuration loading: `rapidkit config validate`

#### Validation Errors

**Symptoms:**

- Configuration validation fails
- Application won't start with validation errors

**Solutions:**

1. Review validation rules in module.yaml
1. Check data types and required fields
1. Use debug mode for detailed error messages
1. Fix configuration according to error messages

### Template Issues

#### Template Rendering Fails

**Symptoms:**

- Code generation fails
- Template syntax errors
- Missing template variables

**Solutions:**

1. Check Jinja2 template syntax
1. Verify all required variables are provided
1. Re-run `rapidkit add module <slug>` with `--plan` (if available) or capture logs and reproduce
   under `scripts/stabilization_runner.py --module <slug>`
1. Check for missing template dependencies

#### Template Not Found

**Symptoms:**

- "Template not found" errors
- Code generation skips templates

**Solutions:**

1. Verify template paths in `module.yaml` and that the referenced files exist under the module's
   `templates/` tree
1. Check template directory structure
1. Ensure templates are committed to repository
1. If the issue is snippet-related, confirm `config/snippets.yaml` references an existing file in
   `templates/snippets/` and run `rapidkit reconcile --verbose` inside the project

### Feature Flag Issues

#### Feature Not Working

**Symptoms:**

- Feature flag enabled but feature not active
- Dependencies not resolved correctly

**Solutions:**

1. Check feature flag configuration
1. Verify all dependencies are installed
1. Check for conflicting features
1. Review environment restrictions
1. Use `rapidkit feature status <feature>` to debug

#### Feature Conflicts

**Symptoms:**

- Cannot enable feature due to conflicts
- "Feature conflict" error messages

**Solutions:**

1. Review feature dependencies and conflicts
1. Disable conflicting features first
1. Check feature flag configuration
1. Use `rapidkit feature check-conflicts <feature>`

### Performance Issues

#### Slow Module Loading

**Symptoms:**

- Application startup is slow
- Module installation takes too long

**Solutions:**

1. Enable lazy loading in module configuration
1. Check caching settings
1. Review preload configurations
1. Monitor resource usage during loading

#### High Memory Usage

**Symptoms:**

- Memory consumption increases over time
- Application becomes unresponsive

**Solutions:**

1. Enable caching with appropriate TTL
1. Configure lazy loading for large modules
1. Check for memory leaks in custom modules
1. Monitor cache sizes and clear if necessary

### Version Compatibility Issues

#### Version Conflicts

**Symptoms:**

- "Version incompatibility" errors
- Module installation fails due to version constraints

**Solutions:**

1. Check compatibility matrices in module.yaml
1. Update conflicting modules to compatible versions
1. Review semantic versioning constraints
1. Use `rapidkit module check-version <module>` to diagnose

#### Breaking Changes

**Symptoms:**

- Application breaks after module update
- API changes cause failures

**Solutions:**

1. Review changelog for breaking changes
1. Follow migration guides
1. Update dependent code
1. Test thoroughly after updates

### Database Issues

#### Connection Failures

**Symptoms:**

- Database modules fail to connect
- Connection timeout errors

**Solutions:**

1. Verify database credentials
1. Check network connectivity
1. Review connection pool settings
1. Test database connectivity manually

#### Migration Issues

**Symptoms:**

- Database migrations fail
- Schema conflicts

**Solutions:**

1. Backup database before migrations
1. Check migration dependencies
1. Review migration scripts
1. Rollback if necessary

### Security Issues

#### Access Control Problems

**Symptoms:**

- Authentication/authorization failures
- Permission denied errors

**Solutions:**

1. Verify security module configuration
1. Check user roles and permissions
1. Review security policies
1. Test authentication flows

#### Encrypted Configuration Issues

**Symptoms:**

- Cannot decrypt configuration values
- Encryption key errors

**Solutions:**

1. Verify encryption keys
1. Check key rotation policies
1. Test encryption/decryption manually
1. Review encryption configuration

## Debug and Diagnostic Tools

### Environment diagnostics

```bash
rapidkit doctor check
```

### Module discovery and metadata

```bash
rapidkit modules list
rapidkit modules search <query>
rapidkit modules info <module>
```

### Install / dependency convergence

```bash
rapidkit add module <module> --profile <kit>
rapidkit add module <module> --profile <kit> --with-deps
```

### Snippet convergence and recovery

```bash
rapidkit reconcile --verbose
rapidkit reconcile --plan
rapidkit rollback snippet --key <snippet_id>::<filename>
```

### Uninstall (remove generated files)

```bash
rapidkit uninstall module <module>
```

<!-- Legacy/obsolete commands and recovery procedures removed for accuracy.
The RapidKit CLI is the source of truth; prefer `rapidkit --help` for the complete command list.
-->

### Configuration Recovery

If something looks "stuck" or inconsistent after installs/uninstalls:

1. Run diagnostics and converge snippets:

   ```bash
   rapidkit doctor check
   rapidkit reconcile --verbose
   ```

1. Inspect `.rapidkit/snippet_registry.json` for `pending/failed/conflicted` entries.

1. If a single snippet is problematic, roll it back and re-run reconcile.

### System Recovery

If a project environment is badly corrupted, the most reliable recovery is:

1. Create a fresh project (same kit/profile)
1. Reinstall the same module set
1. Compare diffs against the broken project to identify the first divergence

## Prevention Best Practices

### Regular Maintenance

1. **Update regularly**: Keep modules and core system updated
1. **Monitor health**: Run `rapidkit doctor check` regularly
1. **Backup configurations**: Maintain configuration backups
1. **Test updates**: Test in staging before production updates

### Development Practices

1. **Version control**: Keep configurations in version control
1. **Test thoroughly**: Test module changes extensively
1. **Document changes**: Document configuration changes
1. **Use validation**: Enable strict validation in development

### Monitoring

1. **Set up alerts**: Monitor for critical errors
1. **Log analysis**: Regularly review logs for issues
1. **Performance monitoring**: Monitor system performance
1. **Capacity planning**: Plan for growth and scaling

## Getting Help

### Community Support

- [GitHub Discussions](https://github.com/getrapidkit/rapidkit-core/discussions)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/rapidkit)
- [Discord Community](https://discord.gg/getrapidkit)

### Professional Support

- [Enterprise Support](https://support.getrapidkit.com)
- [Consulting Services](https://consulting.getrapidkit.com)
- [Training Programs](https://training.getrapidkit.com)

### Reporting Issues

When reporting issues, include:

1. **System information**: OS, Python version, RapidKit version
1. **Module list**: Installed modules and versions
1. **Configuration**: Relevant configuration (redact sensitive data)
1. **Logs**: Error logs and debug information
1. **Steps to reproduce**: Detailed reproduction steps
1. **Expected vs actual**: What you expected vs what happened

## Emergency Contacts

- **Security issues**: [security@getrapidkit.com](mailto:security@getrapidkit.com)
- **System down**: [emergency@getrapidkit.com](mailto:emergency@getrapidkit.com)
- **General support**: [support@getrapidkit.com](mailto:support@getrapidkit.com)
