"""Domain exceptions for the AI Knowledge Generator.

This module contains custom exceptions that represent domain-specific error
conditions. These exceptions are used to handle business logic errors in a
type-safe way.
"""


class DomainException(Exception):
    """Base class for all domain exceptions."""
    pass


class InvalidExpertiseLevelError(DomainException):
    """Raised when an invalid expertise level is provided."""
    def __init__(self, level: str, valid_levels: list[str]):
        super().__init__(
            f"Invalid expertise level: {level}. "
            f"Must be one of: {', '.join(valid_levels)}"
        )


class InvalidCategoryError(DomainException):
    """Raised when an invalid category is provided."""
    def __init__(self, category: str, valid_categories: list[str]):
        super().__init__(
            f"Invalid category: {category}. "
            f"Must be one of: {', '.join(valid_categories)}"
        )


class ContentGenerationError(DomainException):
    """Raised when content generation fails."""
    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(message)
        self.original_error = original_error


class FileConversionError(DomainException):
    """Raised when file conversion fails."""
    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(message)
        self.original_error = original_error 