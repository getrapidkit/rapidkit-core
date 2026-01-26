"""Override contracts for Oauth."""

from core.services.override_contracts import ConfigurableOverrideMixin


class OauthOverrides(ConfigurableOverrideMixin):
    """Extend or customize generated behaviour for Oauth."""

    # def custom_method(self, *args, **kwargs):
    #     """Example override."""
    #     original = self.call_original("custom_method", *args, **kwargs)
    #     return original
