"""Override contracts for Connector Hub."""

from core.services.override_contracts import ConfigurableOverrideMixin


class ConnectorHubOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Connector Hub."""

    # def custom_method(self, *args, **kwargs):
    #     """Example override."""
    #     original = self.call_original("custom_method", *args, **kwargs)
    #     return original
