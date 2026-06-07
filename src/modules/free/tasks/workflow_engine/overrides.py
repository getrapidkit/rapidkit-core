"""Override contracts for Workflow Engine."""

from core.services.override_contracts import ConfigurableOverrideMixin


class WorkflowEngineOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Workflow Engine."""

    # def custom_method(self, *args, **kwargs):
    #     """Example override."""
    #     original = self.call_original("custom_method", *args, **kwargs)
    #     return original
