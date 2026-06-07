"""Override contracts for Document Pipeline."""

from core.services.override_contracts import ConfigurableOverrideMixin


class DocumentPipelineOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Document Pipeline."""

    # def custom_method(self, *args, **kwargs):
    #     """Example override."""
    #     original = self.call_original("custom_method", *args, **kwargs)
    #     return original
