"""Override contracts for Support Center."""

from core.services.override_contracts import ConfigurableOverrideMixin


class SupportCenterOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Support Center."""

    # def custom_method(self, *args, **kwargs):
    #     """Example override."""
    #     original = self.call_original("custom_method", *args, **kwargs)
    #     return original
