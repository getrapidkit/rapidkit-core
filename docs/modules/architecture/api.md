# RapidKit Modular System - API Reference

This page is **CLI-first**.

- The stable public contract is the RapidKit CLI (`rapidkit ...`).
- Internal Python APIs change more frequently and are not considered a stable integration surface.

If you are building automation, prefer shelling out to the CLI and consuming JSON outputs (where
available).

## Primary CLI commands

- **Discovery**: `rapidkit modules list`, `rapidkit modules search <query>`,
  `rapidkit modules info <slug-or-name> [--json]`
- **Install**: `rapidkit add module <slug-or-name> --profile <kit>`
- **Reconcile**: `rapidkit reconcile [--verbose]`, `rapidkit reconcile --plan` (diff-only, no
  writes)
- **Recover**: `rapidkit rollback snippet --key <snippet_id>::<filename>`,
  `rapidkit reconcile --resolve-key <key> --resolve-to pending|failed`

## Internal services (best-effort reference)

These are useful for contributors working inside this repo:

- **Dependencies**: `core.services.module_manifest.load_all_manifests`,
  `core.services.module_manifest.compute_install_order` (canonical field: `module.yaml: depends_on`)
- **Snippets**: `core.services.snippet_injector` (reconcile/plan/rollback/conflict), project state
  `.rapidkit/snippet_registry.json`, audit `.rapidkit/audit/snippet_injections.jsonl`

For the full snippet architecture, see
[docs/modules/architecture/snippet-architecture.md](snippet-architecture.md).

<!--

## Core Classes and Functions

### ModuleManager

Main class for managing modules in the RapidKit system.

#### Constructor

```text
ModuleManager(config_path: str = "config/modules.yaml")
```

**Parameters:**

- `config_path`: Path to the modules configuration file

#### Methods

##### `load_modules() -> Dict[str, Module]`

Loads all configured modules.

**Returns:** Dictionary mapping module names to Module instances

**Raises:** ModuleLoadError if loading fails

##### `install_module(name: str, version: str = None, profile: str = None) -> bool`

Installs a module with optional version and profile.

**Parameters:**

- `name`: Module name to install
- `version`: Specific version to install (default: latest)
- `profile`: Installation profile to use

**Returns:** True if installation successful

**Raises:** ModuleInstallError if installation fails

##### `remove_module(name: str) -> bool`

Removes an installed module.

**Parameters:**

- `name`: Module name to remove

**Returns:** True if removal successful

**Raises:** ModuleRemoveError if removal fails

##### `validate_module(name: str) -> ValidationResult`

Validates a module's configuration and dependencies.

**Parameters:**

- `name`: Module name to validate

**Returns:** ValidationResult with success status and error messages

##### `check_compatibility(module1: str, module2: str) -> CompatibilityResult`

Checks compatibility between two modules.

**Parameters:**

- `module1`: First module name
- `module2`: Second module name

**Returns:** CompatibilityResult with compatibility status

##### `get_module_info(name: str) -> ModuleInfo`

Retrieves detailed information about a module.

**Parameters:**

- `name`: Module name

**Returns:** ModuleInfo object with module metadata

**Raises:** ModuleNotFoundError if module doesn't exist

### Module Class

Represents an individual module.

#### Properties

- `name`: Module name
- `category`: Module category
- `version`: Module version
- `description`: Module description
- `dependencies`: List of module dependencies
- `features`: List of supported features

#### Methods

##### `is_compatible(system_version: str) -> bool`

Checks if module is compatible with system version.

**Parameters:**

- `system_version`: System version to check against

**Returns:** True if compatible

##### `get_template_paths() -> List[str]`

Gets all template paths for the module.

**Returns:** List of template file paths

##### `validate_config(config: dict) -> bool`

Validates module configuration.

**Parameters:**

- `config`: Configuration dictionary to validate

**Returns:** True if valid

**Raises:** ValidationError with details if invalid

### FeatureManager

Manages feature flags and their dependencies.

#### Methods

##### `enable_feature(name: str, context: dict = None) -> bool`

Enables a feature flag.

**Parameters:**

- `name`: Feature name to enable
- `context`: Context dictionary for conditional features

**Returns:** True if enabled successfully

**Raises:** FeatureDependencyError if dependencies not met

##### `disable_feature(name: str) -> bool`

Disables a feature flag.

**Parameters:**

- `name`: Feature name to disable

**Returns:** True if disabled successfully

##### `is_feature_enabled(name: str, context: dict = None) -> bool`

Checks if a feature is enabled.

**Parameters:**

- `name`: Feature name to check
- `context`: Context for conditional evaluation

**Returns:** True if feature is enabled

##### `check_feature_conflicts(feature: str, enabled_features: List[str]) -> List[str]`

Checks for conflicts with enabled features.

**Parameters:**

- `feature`: Feature to check
- `enabled_features`: List of currently enabled features

**Returns:** List of conflicting features

##### `get_feature_dependencies(feature: str) -> List[str]`

Gets all dependencies for a feature.

**Parameters:**

- `feature`: Feature name

**Returns:** List of required dependencies

### TemplateEngine

Handles template rendering and code generation.

#### Methods

##### `render_template(template_path: str, context: dict) -> str`

Renders a Jinja2 template with given context.

**Parameters:**

- `template_path`: Path to template file
- `context`: Context dictionary for template rendering

**Returns:** Rendered template content

**Raises:** TemplateRenderError if rendering fails

##### `validate_template(template_path: str) -> bool`

Validates template syntax.

**Parameters:**

- `template_path`: Path to template file

**Returns:** True if template is valid

##### `get_template_variables(template_path: str) -> List[str]`

Extracts required variables from template.

**Parameters:**

- `template_path`: Path to template file

**Returns:** List of required variable names

### ConfigurationManager

Manages multi-source configuration loading.

#### Methods

##### `load_config() -> dict`

Loads configuration from all configured sources.

**Returns:** Merged configuration dictionary

**Raises:** ConfigurationError if loading fails

##### `get_value(key: str, default=None) -> Any`

Retrieves a configuration value.

**Parameters:**

- `key`: Dot-separated configuration key
- `default`: Default value if key not found

**Returns:** Configuration value or default

##### `set_value(key: str, value: Any) -> None`

Sets a configuration value.

**Parameters:**

- `key`: Configuration key
- `value`: Value to set

##### `validate_config(config: dict) -> ValidationResult`

Validates configuration against rules.

**Parameters:**

- `config`: Configuration to validate

**Returns:** ValidationResult with validation status

##### `reload_config() -> None`

Forces reload of all configuration sources.

##### `watch_config(callback: Callable) -> None`

Registers callback for configuration changes.

**Parameters:**

- `callback`: Function to call on config changes

### ValidationEngine

Handles configuration and module validation.

#### Methods

##### `validate_module_config(module: str, config: dict) -> ValidationResult`

Validates module-specific configuration.

**Parameters:**

- `module`: Module name
- `config`: Configuration to validate

**Returns:** ValidationResult

##### `validate_dependencies(modules: List[str]) -> DependencyResult`

Validates module dependencies.

**Parameters:**

- `modules`: List of module names

**Returns:** DependencyResult with validation status

##### `validate_compatibility(modules: List[str]) -> CompatibilityResult`

Validates module compatibility.

**Parameters:**

- `modules`: List of module names

**Returns:** CompatibilityResult

### RollbackManager

Handles system rollback operations.

#### Methods

##### `create_restore_point(name: str) -> str`

Creates a system restore point.

**Parameters:**

- `name`: Name for the restore point

**Returns:** Restore point ID

##### `rollback_to_point(restore_point_id: str) -> bool`

Rolls back system to a restore point.

**Parameters:**

- `restore_point_id`: ID of restore point to rollback to

**Returns:** True if rollback successful

**Raises:** RollbackError if rollback fails

##### `list_restore_points() -> List[RestorePoint]`

Lists available restore points.

**Returns:** List of RestorePoint objects

##### `cleanup_old_restore_points(keep_days: int = 30) -> int`

Removes old restore points.

**Parameters:**

- `keep_days`: Number of days to keep restore points

**Returns:** Number of restore points removed

## Data Structures

### ModuleInfo

```python
@dataclass
class ModuleInfo:
    name: str
    category: str
    version: str
    description: str
    author: str
    license: str
    homepage: str
    repository: str
    issues: str
    documentation: str
    compatibility: CompatibilityMatrix
    features: List[str]
    dependencies: List[str]
    conflicts: List[str]
    testing: TestingConfig
    documentation_info: DocumentationConfig
    changelog: List[ChangelogEntry]
    validation: ValidationConfig
    rollback: RollbackConfig
    performance: PerformanceConfig
    support: SupportConfig
```

### CompatibilityMatrix

```python
@dataclass
class CompatibilityMatrix:
    python: str
    rapidkit: str
    dependencies: Dict[str, str]
```

### FeatureConfig

```python
@dataclass
class FeatureConfig:
    enabled: bool
    dependencies: List[str]
    conflicts: List[str]
    environment: Optional[str]
    profiles: List[str]
    conditions: Dict[str, Any]
```

### ValidationResult

```python
@dataclass
class ValidationResult:
    valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
```

## CLI Commands

### Module Commands

```bash
# Install module
rapidkit module install <name> [--version VERSION] [--profile PROFILE]

# Remove module
rapidkit module remove <name>

# List modules
rapidkit module list [--installed] [--available] [--category CATEGORY]

# Validate module
rapidkit module validate <name>

# Update module registry
rapidkit module update-registry

# Check compatibility
rapidkit module check-compatibility <module1> <module2>
```

### Feature Commands

```bash
# Enable feature
rapidkit feature enable <name>

# Disable feature
rapidkit feature disable <name>

# List features
rapidkit feature list [--enabled] [--available]

# Check conflicts
rapidkit feature check-conflicts <feature>
```

### Configuration Commands

```bash
# Validate configuration
rapidkit config validate

# Show configuration
rapidkit config show [--source SOURCE]

# Reload configuration
rapidkit config reload

# Reset configuration
rapidkit config reset
```

### System Commands

```bash
# System health check
rapidkit system health

# System status
rapidkit system status

# Create backup
rapidkit backup create <name>

# Restore from backup
rapidkit backup restore <name>
```

## Error Classes

### ModuleLoadError

Raised when module loading fails.

**Attributes:**

- `module_name`: Name of the module that failed to load
- `reason`: Reason for the failure

### ModuleInstallError

Raised when module installation fails.

**Attributes:**

- `module_name`: Name of the module that failed to install
- `reason`: Reason for the failure
- `dependencies`: Missing dependencies

### ValidationError

Raised when validation fails.

**Attributes:**

- `field`: Field that failed validation
- `value`: Invalid value
- `rule`: Validation rule that was violated

### FeatureDependencyError

Raised when feature dependencies are not met.

**Attributes:**

- `feature`: Feature name
- `missing_dependencies`: List of missing dependencies

### ConfigurationError

Raised when configuration loading fails.

**Attributes:**

- `source`: Configuration source that failed
- `reason`: Reason for the failure

### TemplateRenderError

Raised when template rendering fails.

**Attributes:**

- `template_path`: Path to the failing template
- `context`: Context that was being used
- `error`: Underlying rendering error

## Constants

### Module Categories

```python
MODULE_CATEGORIES = [
    "core",
    "database",
    "cache",
    "observability",
    "security",
    "business",
    "communication",
    "documentation",
]
```

### Feature Types

```python
FEATURE_TYPES = [
    "boolean",  # Simple on/off feature
    "conditional",  # Feature with conditions
    "profile",  # Profile-specific feature
    "environment",  # Environment-specific feature
]
```

### Validation Rules

```python
VALIDATION_RULES = [
    "required",
    "type",
    "min_length",
    "max_length",
    "min_value",
    "max_value",
    "pattern",
    "custom",
]
```

## Examples

### Installing a Module

```python
from rapidkit.modules import ModuleManager

manager = ModuleManager()
result = manager.install_module("settings", version="1.3.0")

if result:
    print("Settings module installed successfully")
else:
    print("Installation failed")
```

### Working with Features

```python
from rapidkit.features import FeatureManager

feature_manager = FeatureManager()

# Enable a feature
feature_manager.enable_feature("advanced_caching")

# Check if feature is enabled
if feature_manager.is_feature_enabled("advanced_caching"):
    print("Advanced caching is active")
```

### Configuration Management

```python
from rapidkit.config import ConfigurationManager

config_manager = ConfigurationManager()

# Load configuration
config = config_manager.load_config()

# Get a value
db_host = config_manager.get_value("database.host", "localhost")

# Set a value
config_manager.set_value("app.debug", True)
```

### Template Rendering

```python
from rapidkit.templates import TemplateEngine

template_engine = TemplateEngine()

# Render a template
context = {"app_name": "MyApp", "version": "1.0.0"}
content = template_engine.render_template("templates/app.py.j2", context)

# Write to file
with open("src/app.py", "w") as f:
    f.write(content)
```

### Validation

```python
from rapidkit.validation import ValidationEngine

validation_engine = ValidationEngine()

# Validate module configuration
result = validation_engine.validate_module_config("settings", config)

if result.valid:
    print("Configuration is valid")
else:
    print("Validation errors:", result.errors)
```

This API reference covers the core components of the RapidKit modular system. For more detailed
examples and advanced usage, see the [documentation](docs/) directory.

-->
