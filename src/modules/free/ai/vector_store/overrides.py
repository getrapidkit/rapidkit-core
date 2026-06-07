"""Override contracts for Vector Store."""

from core.services.override_contracts import ConfigurableOverrideMixin


class VectorStoreOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Vector Store."""

    # def custom_method(self, *args, **kwargs):
    #     """Example override."""
    #     original = self.call_original("custom_method", *args, **kwargs)
    #     return original
