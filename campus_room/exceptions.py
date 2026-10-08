class BookingError(Exception):
    """Raised when a reservation cannot be created."""


class ConflictError(BookingError):
    """Raised when two bookings overlap in the same room."""


class BookingLimitError(BookingError):
    """Raised when a user has reached their role's booking cap."""
