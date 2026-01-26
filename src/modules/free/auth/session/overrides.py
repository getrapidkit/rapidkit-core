"""Override contracts for Session."""

from core.services.override_contracts import ConfigurableOverrideMixin


class SessionOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Session."""

    # def custom_method(self, *args, **kwargs):
    #     """Example override."""
    #     original = self.call_original("custom_method", *args, **kwargs)
    #     return original
