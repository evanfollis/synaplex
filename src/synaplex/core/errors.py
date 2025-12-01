# synaplex/core/errors.py


class SynaplexError(Exception):
    """Base exception for Synaplex."""


class RoutingError(SynaplexError):
    """Raised when the runtime cannot route a message or tick."""


class ConfigError(SynaplexError):
    """Raised for invalid graph/world configuration."""
