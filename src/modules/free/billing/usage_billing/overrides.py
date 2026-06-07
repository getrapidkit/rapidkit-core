"""Override contracts for Usage Billing."""

from core.services.override_contracts import ConfigurableOverrideMixin


class UsageBillingOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Usage Billing."""

    # def custom_method(self, *args, **kwargs):
    #     """Example override."""
    #     original = self.call_original("custom_method", *args, **kwargs)
    #     return original
