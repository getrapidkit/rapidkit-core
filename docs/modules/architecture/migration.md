# RapidKit Modular System - Migration Guide

This guide helps you migrate from older versions of RapidKit to the new enterprise-grade modular
system.

## Overview

The v2.0.0 release introduces significant improvements to the modular architecture, including
categorized module organization, comprehensive metadata, advanced feature flags, and
enterprise-grade features.

## Migration Checklist

- [ ] Backup all configurations and data
- [ ] Review breaking changes
- [ ] Update CLI to latest version
- [ ] Migrate module structure
- [ ] Update configurations
- [ ] Test thoroughly
- [ ] Deploy to production

## Breaking Changes in v2.0.0

### Module Organization

- **Old**: Flat module structure
- **New**: Categorized module directories (core/, database/, cache/, etc.)

**Migration Required**: Yes

### Module Registry

- **Old**: Basic module metadata
- **New**: Comprehensive metadata with compatibility, testing, documentation

**Migration Required**: Yes

### Feature Flags

- **Old**: Simple enable/disable flags
- **New**: Advanced flags with dependencies, conflicts, environments

**Migration Required**: Yes

### Configuration System

- **Old**: Basic configuration loading
- **New**: Multi-source configuration with validation and hot reload

**Migration Required**: Partial (enhanced features available)

## Step-by-Step Migration

### Step 1: Preparation

1. **Backup Everything**

   ```bash
   # Backup configurations
   cp -r config/ config.backup/

   # Backup data if applicable
   # (depends on your modules)
   ```

1. **Update CLI**

   ```bash
   pip install --upgrade rapidkit-cli
   rapidkit --version  # Verify update
   ```

1. **Check Current State**

   ```bash
   rapidkit system status
   rapidkit module list --installed
   ```

### Step 2: Module Structure Migration

1. **Identify Installed Modules**

   ```bash
   rapidkit module list --installed > installed_modules.txt
   ```

1. **Remove Old Modules**

   ```bash
   # Remove all installed modules
   for module in $(rapidkit module list --installed --quiet); do
     rapidkit module remove $module
   done
   ```

1. **Update Module Registry**

   ```bash
   rapidkit module update-registry
   ```

1. **Reorganize Module Directories** The new structure organizes modules into categories. The CLI
   will handle this automatically during installation.

### Step 3: Configuration Migration

1. **Update Configuration Format**

   ```yaml
   # Old format
   modules:
     settings:
       enabled: true

   # New format
   modules:
     settings:
       category: core
       version: "1.3.0"
       features:
         - multi-source-config
         - hot-reload
   ```

1. **Migrate Environment Variables**

   ```bash
   # Old prefix
   export APP_DATABASE_HOST=localhost

   # New prefix
   export RAPIDKIT_DATABASE__HOST=localhost
   ```

1. **Update Feature Flags**

   ```yaml
   # Old format
   features:
     caching: true

   # New format
   features:
     advanced_caching:
       enabled: true
       dependencies:
         - redis
       environment: production
   ```

### Step 4: Reinstall Modules

1. **Install Core Modules First**

   ```bash
   rapidkit module install settings
   rapidkit module install logging
   ```

1. **Install Database Modules**

   ```bash
   rapidkit module install database/postgres
   # or
   rapidkit module install database/mysql
   ```

1. **Install Other Modules**

   ```bash
   rapidkit module install cache/redis
   rapidkit module install observability/prometheus
   ```

### Step 5: Validation and Testing

1. **Validate Configuration**

   ```bash
   rapidkit config validate
   ```

1. **Check Module Compatibility**

   ```bash
   rapidkit module validate-all
   ```

1. **Run Tests**

   ```bash
   rapidkit test run
   ```

1. **Check System Health**

   ```bash
   rapidkit system health
   ```

## Module-Specific Migrations

### Settings Module Migration

**Changes:**

- Environment variable prefix: `APP_` → `RAPIDKIT_`
- Configuration validation now stricter
- Hot reload configuration format changed

**Migration Steps:**

1. Update environment variables
1. Review validation rules
1. Update hot reload configuration
1. Test configuration loading

### Database Module Migration

**Changes:**

- Connection configuration format updated
- Migration system enhanced
- Connection pooling configuration changed

**Migration Steps:**

1. Update database connection strings
1. Review migration configurations
1. Test database connectivity
1. Run migrations

### Cache Module Migration

**Changes:**

- Cache configuration format updated
- New caching strategies available
- Performance optimizations added

**Migration Steps:**

1. Update cache configurations
1. Choose appropriate caching strategy
1. Test cache functionality
1. Monitor performance

## Troubleshooting Migration Issues

### Common Problems

#### Module Installation Fails

```bash
# Check dependencies
rapidkit module check-dependencies <module>

# Force installation (use carefully)
rapidkit module install <module> --force
```

#### Configuration Validation Errors

```bash
# Get detailed validation errors
rapidkit config validate --verbose

# Reset to defaults and rebuild
rapidkit config reset
```

#### Feature Flag Conflicts

```bash
# Check feature conflicts
rapidkit feature check-conflicts <feature>

# Resolve conflicts manually
rapidkit feature disable <conflicting-feature>
```

### Rollback Procedures

If migration fails, rollback to previous state:

1. **Stop Application**

   ```bash
   rapidkit app stop
   ```

1. **Restore Backup**

   ```bash
   cp -r config.backup/* config/
   ```

1. **Reinstall Old Versions**

   ```bash
   rapidkit module install <module>@<old-version>
   ```

1. **Restart Application**

   ```bash
   rapidkit app start
   ```

## Advanced Migration Scenarios

### Large-Scale Migration

For large deployments:

1. **Create Migration Plan**

   - Identify all affected systems
   - Plan downtime windows
   - Prepare rollback procedures

1. **Staged Migration**

   - Migrate development environments first
   - Test thoroughly in staging
   - Plan production migration during low-traffic periods

1. **Parallel Migration**

   - Migrate different services independently
   - Use feature flags to control rollout
   - Monitor closely during transition

### Custom Module Migration

If you have custom modules:

1. **Update Module Structure**

   - Move to appropriate category directory
   - Update `module.yaml` with comprehensive metadata
   - Reorganize templates according to new structure

1. **Update Templates**

   - Migrate to new template directory structure
   - Update Jinja2 syntax if needed
   - Test template rendering

1. **Update Documentation**

   - Create comprehensive documentation
   - Add API reference, troubleshooting, migration guide
   - Update README with new features

## Post-Migration Tasks

### Optimization

1. **Enable Performance Features**

   ```yaml
   performance:
     lazy_loading: true
     caching:
       enabled: true
   ```

1. **Configure Monitoring**

   ```bash
   rapidkit module install observability/prometheus
   rapidkit module install observability/opentelemetry
   ```

1. **Set Up Backups**

   ```bash
   rapidkit backup configure
   ```

### Security Hardening

1. **Enable Security Modules**

   ```bash
   rapidkit module install security/jwt
   rapidkit module install security/oauth2
   ```

1. **Configure Encryption**

   ```yaml
   encryption:
     enabled: true
     algorithm: AES-256-GCM
   ```

1. **Set Up Access Controls**

   ```bash
   rapidkit security configure
   ```

### Documentation Updates

1. **Update Runbooks**

   - Document new module management procedures
   - Update troubleshooting guides
   - Create new monitoring dashboards

1. **Team Training**

   - Train developers on new features
   - Update development workflows
   - Document best practices

## Version-Specific Migration Guides

### From v1.5.x to v2.0.0

**Additional Steps:**

- Update feature flag configurations
- Migrate to categorized module structure
- Enable new validation features

### From v1.4.x to v2.0.0

**Additional Steps:**

- Update template structures
- Configure performance optimizations
- Set up monitoring

### From v1.3.x to v2.0.0

**Additional Steps:**

- Complete module reorganization
- Update all configurations
- Test all integrations

## Support and Resources

### Getting Help

- **Migration Support**: migration@getrapidkit.com
- **Documentation**: https://docs.getrapidkit.com/migration
- **Community**: https://github.com/getrapidkit/rapidkit-core/discussions
- **Professional Services**: https://services.getrapidkit.com

### Useful Commands

```bash
# Get migration status
rapidkit migration status

# Validate migration
rapidkit migration validate

# Get migration report
rapidkit migration report

# Rollback migration
rapidkit migration rollback
```

### Key Contacts

- **Technical Lead**: tech-lead@getrapidkit.com
- **Support Team**: support@getrapidkit.com
- **Security Team**: security@getrapidkit.com

Remember: Always test migrations in non-production environments first, and have a rollback plan
ready before starting production migrations.
