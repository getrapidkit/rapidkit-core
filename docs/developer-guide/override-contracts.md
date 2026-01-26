# 🔄 Override Contracts

Override contracts provide a safe mechanism for customizing RapidKit modules without breaking
upgrades. This system allows you to override methods and settings in a way that survives module
updates and maintains compatibility.

## 🎯 Overview

Override contracts solve the common problem of customizing third-party code: how do you modify
behavior without forking or risking breakage on updates? RapidKit's override system provides two
complementary approaches:

1. **Decorator-based overrides**: Use decorators to register custom implementations
1. **Mixin-based inheritance**: Extend classes with override-aware mixins

Both approaches ensure that:

- Original functionality is preserved and accessible
- Overrides are upgrade-safe
- Multiple overrides can coexist
- Compatibility is validated automatically

## 📝 Decorator-Based Overrides

Use decorators when you want to override specific methods or settings from external modules.

### Method Overrides

```python
from rapidkit.core.services.override_contracts import override_method


# Override a specific method
@override_method("Settings.load_config")
def custom_load_config(self):
    """Custom configuration loading logic."""
    config = self.load_config()  # Call original
    config.update({"custom_setting": True})
    return config
```

### Setting Overrides

```python
from rapidkit.core.services.override_contracts import override_setting


# Override a setting value
@override_setting("Settings.DEBUG_MODE")
def custom_debug_mode():
    """Custom debug mode logic."""
    import os

    return os.getenv("MYAPP_DEBUG", "false").lower() == "true"


# Or override with a direct value
@override_setting("Settings.TIMEOUT", 60)
def custom_timeout():
    """Override timeout setting."""
    pass  # Not called when using direct value override
```

## 🧬 Mixin-Based Overrides

Use mixins when you want to create custom classes that extend module behavior through inheritance.

### Basic Method Override

```python
from rapidkit.core.services.override_contracts import ConfigurableOverrideMixin


class CustomService(BaseService, ConfigurableOverrideMixin):
    """Custom service with override support."""

    def make_request(self, url: str) -> Dict[str, Any]:
        """Override request logic with custom behavior."""
        # Call original method
        result = self.call_original("make_request", url)

        # Add custom logic
        result["logged"] = True
        result["custom_header"] = "X-Custom-Service"
        return result
```

### Setting Override with Mixins

```python
class CustomSettingsManager(SettingsManager, ConfigurableOverrideMixin):
    """Settings manager with custom overrides."""

    def __init__(self):
        super().__init__()
        # Original settings are automatically preserved

    def get_custom_setting(self) -> str:
        """Get original setting value."""
        return self.get_original_setting("database_url")
```

## 🔧 Available Mixins

### `OverrideMixin`

Base mixin for method overrides only. Provides:

- `call_original(method_name, *args, **kwargs)`: Call the original method
- Automatic original method storage

### `SettingOverrideMixin`

Mixin for setting overrides only. Provides:

- `get_original_setting(setting_name)`: Get the original setting value
- Automatic setting preservation

### `ConfigurableOverrideMixin`

Combined mixin with full override support. Provides:

- All method override capabilities
- All setting override capabilities
- `get_override_info()`: Get information about applied overrides

## 📋 Best Practices

### 1. Always Call Original Methods

When overriding methods, preserve the original behavior:

```python
# ✅ Good: Preserve original behavior
def custom_validate(self, data):
    result = self.call_original("validate", data)
    # Add custom validation
    return result and self.custom_check(data)


# ❌ Bad: Replace entirely
def custom_validate(self, data):
    return self.custom_check(data)  # Lost original validation
```

### 2. Use Appropriate Override Type

Choose the right approach for your use case:

```python
# Use decorators for simple overrides
@override_setting("Settings.TIMEOUT", 30)
def timeout_override():
    pass


# Use mixins for complex class customization
class CustomLogger(Logger, ConfigurableOverrideMixin):
    def log(self, message, level):
        # Complex custom logic here
        pass
```

### 3. Validate Override Compatibility

Use the validation mixin to check compatibility:

```python
class MyCustomService(BaseService, ValidationOverrideMixin):
    def custom_method(self):
        # Custom implementation
        pass


# Check compatibility
service = MyCustomService()
validation = service.validate_overrides()
if not validation["valid"]:
    print("Override compatibility issues:", validation["errors"])
```

## 🔍 Introspection and Debugging

### Checking Applied Overrides

```python
service = CustomService()
info = service.get_override_info()
print(f"Method overrides: {info['method_overrides']}")
print(f"Setting overrides: {info['setting_overrides']}")
```

### Accessing Original Implementations

```python
# Get original method
original_method = getattr(service, "_original_make_request")

# Get original setting
original_timeout = service.get_original_setting("timeout")
```

## 🚨 Common Pitfalls

### Recursion Errors

Avoid calling the override method from within itself:

```python
# ❌ Bad: Causes recursion
def make_request(self, url):
    return self.make_request(url)  # Calls itself!


# ✅ Good: Call original
def make_request(self, url):
    return self.call_original("make_request", url)
```

### Signature Mismatches

Ensure override methods have compatible signatures:

```python
# Original method
def process_data(self, data: Dict, options: Optional[Dict] = None):
    pass


# ✅ Good: Compatible signature
def process_data(self, data: Dict, options: Optional[Dict] = None):
    return self.call_original("process_data", data, options)


# ❌ Bad: Incompatible signature
def process_data(self, data):  # Missing options parameter
    return self.call_original("process_data", data)
```

## 🔗 Integration with Modules

Override contracts integrate seamlessly with RapidKit's module system. Each module can provide
override contracts that users can customize.

### Module Structure

Modules can include an `overrides.py` file that defines available override points:

```
src/modules/free/essentials/settings/
├── overrides.py          # Override contracts for this module
├── __init__.py
└── ...
```

### Loading Module Overrides

```python
from rapidkit.core.services.override_contracts import (
    load_module_overrides,
    apply_module_overrides,
)

# Load overrides from the settings module
load_module_overrides("settings")

# Or apply overrides directly to a class
EnhancedClass = apply_module_overrides(MyClass, "settings")
```

### Creating Module Overrides

Module authors can define override points in their `overrides.py`:

```python
# In src/modules/free/essentials/settings/overrides.py
from core.services.override_contracts import override_method, override_setting

# Define override points (these are templates for users)
# @override_method("Settings.load_config")
# def custom_load_config(self):
#     config = self.load_config()
#     config.update({"custom_feature": True})
#     return config
```

Users can then create their own overrides that reference these points.

## 📚 Examples

See `core.services.override_contracts.examples` for comprehensive examples of:

- Decorator usage patterns
- Mixin inheritance
- Complex override scenarios
- Error handling and validation

## 🎯 Migration Guide

### From Direct Inheritance

```python
# Old approach (brittle)
class CustomService(BaseService):
    def make_request(self, url):
        # Risk of breaking on updates
        return super().make_request(url)


# New approach (safe)
class CustomService(BaseService, ConfigurableOverrideMixin):
    def make_request(self, url):
        # Safe override with original access
        return self.call_original("make_request", url)
```

### From Monkey Patching

```python
# Old approach (dangerous)
original_method = SomeClass.method
SomeClass.method = custom_method


# New approach (safe)
@override_method("SomeClass.method")
def custom_method(self, *args, **kwargs):
    return self.call_original("method", *args, **kwargs)
```

______________________________________________________________________

Override contracts enable safe, upgrade-compatible customization of RapidKit modules. Use decorators
for simple overrides and mixins for complex class customization. Always preserve original behavior
and validate compatibility.</content>
<parameter name="filePath">/home/debux/WOSP/core/docs/developer-guide/override-contracts.md
