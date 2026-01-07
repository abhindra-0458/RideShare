from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import jwt
from datetime import datetime
import logging
from exceptions import (
    RideShareException, ValidationError, UnauthorizedError,
    JWTError, TokenExpiredError, DatabaseError
)
from response_handler import ApiResponse

logger = logging.getLogger(__name__)

async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler"""
    
    # Log error
    logger.error(
        f"Error: {type(exc).__name__}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
            "client": request.client,
        }
    )
    
    # Handle custom rideshare exceptions
    if isinstance(exc, RideShareException):
        return ApiResponse.error(
            message=exc.message,
            status_code=exc.status_code,
            errors=exc.errors
        )
    
    # Handle JWT errors
    if isinstance(exc, jwt.ExpiredSignatureError):
        return ApiResponse.unauthorized("Token expired")
    
    if isinstance(exc, jwt.InvalidTokenError):
        return ApiResponse.unauthorized("Invalid token")
    
    # Handle database errors
    if isinstance(exc, IntegrityError):
        # Parse database error
        error_info = str(exc.orig)
        if "unique constraint" in error_info:
            return ApiResponse.error(
                "Duplicate entry - resource already exists",
                409
            )
        elif "foreign key constraint" in error_info:
            return ApiResponse.error(
                "Foreign key constraint violation",
                400
            )
        elif "not-null constraint" in error_info:
            return ApiResponse.error(
                "Required field is missing",
                400
            )
        return ApiResponse.error("Database error", 500)
    
    if isinstance(exc, SQLAlchemyError):
        return ApiResponse.error("Database error", 500)
    
    # Handle validation errors
    if isinstance(exc, ValueError):
        return ApiResponse.error(str(exc), 400)
    
    # Default error
    return ApiResponse.error(
        "Internal Server Error",
        500
    )

def install_exception_handlers(app):
    """Install exception handlers to FastAPI app"""
    app.add_exception_handler(RideShareException, exception_handler)
    app.add_exception_handler(Exception, exception_handler)
