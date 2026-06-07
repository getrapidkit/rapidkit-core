"""Override contracts for Llm Gateway."""

from core.services.override_contracts import ConfigurableOverrideMixin


class LlmGatewayOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Llm Gateway."""

    # def custom_method(self, *args, **kwargs):
    #     """Example override."""
    #     original = self.call_original("custom_method", *args, **kwargs)
    #     return original
