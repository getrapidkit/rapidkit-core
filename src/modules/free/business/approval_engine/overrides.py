"""Override contracts for Approval Engine."""

from core.services.override_contracts import ConfigurableOverrideMixin


class ApprovalEngineOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Approval Engine."""

    # def custom_method(self, *args, **kwargs):
    #     """Example override."""
    #     original = self.call_original("custom_method", *args, **kwargs)
    #     return original
