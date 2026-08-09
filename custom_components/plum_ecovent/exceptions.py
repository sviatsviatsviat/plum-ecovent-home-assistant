"""Exceptions for the Plum ecoVENT API client."""


class PlumEconetError(Exception):
    """Base error for the Plum ecoVENT API client."""


class PlumEconetAuthError(PlumEconetError):
    """Raised when the module rejects credentials (HTTP 401)."""


class PlumEconetConnectionError(PlumEconetError):
    """Raised when the module cannot be reached or returns a non-success status."""


class PlumEconetInsecureHttpError(PlumEconetConnectionError):
    """Raised when cleartext HTTP is used without an explicit opt-in."""
