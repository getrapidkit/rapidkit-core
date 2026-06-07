"""Override contracts for Forms Engine."""

from core.services.override_contracts import ConfigurableOverrideMixin


class FormsEngineOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Forms Engine."""

    # def custom_method(self, *args, **kwargs):
    #     """Example override."""
    #     original = self.call_original("custom_method", *args, **kwargs)
    #     return original
