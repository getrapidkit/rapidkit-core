"""Override contracts for Rag Pipeline."""

from core.services.override_contracts import ConfigurableOverrideMixin


class RagPipelineOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Rag Pipeline."""

    # def custom_method(self, *args, **kwargs):
    #     """Example override."""
    #     original = self.call_original("custom_method", *args, **kwargs)
    #     return original
