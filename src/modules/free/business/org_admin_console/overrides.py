"""Override contracts for Org Admin Console."""

from core.services.override_contracts import ConfigurableOverrideMixin


class OrgAdminConsoleOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Org Admin Console."""

    # def custom_method(self, *args, **kwargs):
    #     """Example override."""
    #     original = self.call_original("custom_method", *args, **kwargs)
    #     return original
