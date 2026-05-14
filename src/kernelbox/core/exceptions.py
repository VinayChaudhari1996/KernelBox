class KernelBoxError(Exception):
    """Base exception for package-level failures."""


class KernelNotFound(KernelBoxError):
    """Raised when a kernel alias or ID is unknown."""


class KernelAlreadyExists(KernelBoxError):
    """Raised when a kernel alias would collide with an existing record."""

