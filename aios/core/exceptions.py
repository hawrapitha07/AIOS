"""
Custom exceptions for AIOS platform.
"""


class AIOSException(Exception):
    """Base exception for AIOS platform."""
    pass


class ConfigurationError(AIOSException):
    """Raised when there's an error in configuration."""
    pass


class WorkflowNotFoundError(AIOSException):
    """Raised when a requested workflow is not found."""
    pass


class ModelProviderError(AIOSException):
    """Raised when there's an error with model provider."""
    pass


class ProjectError(AIOSException):
    """Raised when there's an error with project operations."""
    pass


class ManagerError(AIOSException):
    """Raised when there's an error in manager operations."""
    pass