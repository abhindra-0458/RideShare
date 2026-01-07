from typing import Optional, List, Dict, Any

class RideShareException(Exception):
    """Base exception for rideshare app"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        errors: Optional[List[Dict[str, str]]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.errors = errors
        super().__init__(self.message)

class ValidationError(RideShareException):
    """Validation error exception"""
    
    def __init__(
        self,
        message: str = "Validation Error",
        errors: Optional[List[Dict[str, str]]] = None
    ):
        super().__init__(message, 400, errors)

class UnauthorizedError(RideShareException):
    """Unauthorized exception"""
    
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, 401)

class ForbiddenError(RideShareException):
    """Forbidden exception"""
    
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, 403)

class NotFoundError(RideShareException):
    """Not found exception"""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, 404)

class ConflictError(RideShareException):
    """Conflict exception"""
    
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message, 409)

class BadRequestError(RideShareException):
    """Bad request exception"""
    
    def __init__(self, message: str = "Bad request"):
        super().__init__(message, 400)

class DatabaseError(RideShareException):
    """Database error exception"""
    
    def __init__(self, message: str = "Database error", original_error: Optional[Exception] = None):
        if original_error:
            # Handle specific database errors
            if hasattr(original_error, 'code'):
                if original_error.code == '23505':  # Unique constraint
                    super().__init__("Duplicate entry - resource already exists", 409)
                elif original_error.code == '23503':  # Foreign key constraint
                    super().__init__("Foreign key constraint violation", 400)
                elif original_error.code == '23502':  # Not null constraint
                    super().__init__("Required field is missing", 400)
                else:
                    super().__init__(message, 500)
            else:
                super().__init__(message, 500)
        else:
            super().__init__(message, 500)

class JWTError(RideShareException):
    """JWT error exception"""
    
    def __init__(self, message: str = "Invalid token"):
        super().__init__(message, 401)

class TokenExpiredError(RideShareException):
    """Token expired exception"""
    
    def __init__(self, message: str = "Token expired"):
        super().__init__(message, 401)

class RideNotAvailableError(RideShareException):
    """Ride not available exception"""
    
    def __init__(self, message: str = "Ride not available"):
        super().__init__(message, 400)

class RideFullError(RideShareException):
    """Ride full exception"""
    
    def __init__(self, message: str = "Ride is full"):
        super().__init__(message, 400)

class AlreadyParticipantError(RideShareException):
    """Already participant exception"""
    
    def __init__(self, message: str = "User is already a participant"):
        super().__init__(message, 400)

class NotParticipantError(RideShareException):
    """Not participant exception"""
    
    def __init__(self, message: str = "User is not a participant in this ride"):
        super().__init__(message, 400)
