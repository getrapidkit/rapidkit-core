"""Override contracts for Prompt Ops."""

from core.services.override_contracts import ConfigurableOverrideMixin


class PromptOpsOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Prompt Ops."""

    # def custom_method(self, *args, **kwargs):
    #     """Example override."""
    #     original = self.call_original("custom_method", *args, **kwargs)
    #     return original
