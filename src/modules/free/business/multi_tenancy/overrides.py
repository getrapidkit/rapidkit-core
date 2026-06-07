"""Override contracts for Multi Tenancy."""

from core.services.override_contracts import ConfigurableOverrideMixin


class MultiTenancyOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Multi Tenancy."""

    # def custom_method(self, *args, **kwargs):
    #     """Example override."""
    #     original = self.call_original("custom_method", *args, **kwargs)
    #     return original
