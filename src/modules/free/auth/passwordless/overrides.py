"""Override contracts for Passwordless."""

from core.services.override_contracts import ConfigurableOverrideMixin


class PasswordlessOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Passwordless."""

    # def custom_method(self, *args, **kwargs):
    #     """Example override."""
    #     original = self.call_original("custom_method", *args, **kwargs)
    #     return original
