class VisualGuardError(Exception):
    """Base exception for Visual Guard library."""
    pass

class ImageLoadError(VisualGuardError):
    """Raised when an image cannot be loaded or processed."""
    pass

class ComparisonError(VisualGuardError):
    """Raised when image comparison fails or encounters an error."""
    pass

class BaselineMissingError(VisualGuardError):
    """Raised when a baseline image is missing and cannot be created automatically."""
    pass
