"""Override contracts for Agent Runtime."""

from core.services.override_contracts import ConfigurableOverrideMixin


class AgentRuntimeOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Agent Runtime."""

    # def custom_method(self, *args, **kwargs):
    #     """Example override."""
    #     original = self.call_original("custom_method", *args, **kwargs)
    #     return original
