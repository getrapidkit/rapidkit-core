"""Override contracts for Audit Policy."""

from core.services.override_contracts import ConfigurableOverrideMixin


class AuditPolicyOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Audit Policy."""

    # def custom_method(self, *args, **kwargs):
    #     """Example override."""
    #     original = self.call_original("custom_method", *args, **kwargs)
    #     return original
