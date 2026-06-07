"""Override contracts for Event Bus."""

from core.services.override_contracts import ConfigurableOverrideMixin


class EventBusOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Event Bus."""

    # def custom_method(self, *args, **kwargs):
    #     """Example override."""
    #     original = self.call_original("custom_method", *args, **kwargs)
    #     return original
