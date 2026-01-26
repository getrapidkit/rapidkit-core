# core/exceptions.py
class RapidKitError(Exception):
    """Base exception for RapidKit"""

    pass


class KitNotFoundError(RapidKitError):
    """Raised when a requested kit is not found"""

    pass


class InvalidKitError(RapidKitError):
    """Raised when a kit is invalid or malformed"""

    pass


class ValidationError(RapidKitError):
    """Raised when input validation fails"""

    pass


class TemplateError(RapidKitError):
    """Raised when template rendering fails"""

    pass
