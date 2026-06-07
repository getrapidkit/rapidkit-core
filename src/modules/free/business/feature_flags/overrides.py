"""Override contracts for Feature Flags."""

from core.services.override_contracts import ConfigurableOverrideMixin


class FeatureFlagsOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Feature Flags."""

    # def custom_method(self, *args, **kwargs):
    #     """Example override."""
    #     original = self.call_original("custom_method", *args, **kwargs)
    #     return original
