from fastapi.responses import JSONResponse
from typing import Any, Optional, List, Dict
from datetime import datetime
from schemas import ErrorDetail, SuccessResponse, ErrorResponse

class ApiResponse:
    """Standard API response formatter"""

    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
        status_code: int = 200
    ) -> JSONResponse:
        """Return success response"""
        response = {
            "success": True,
            "message": message,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        return JSONResponse(content=response, status_code=status_code)

    @staticmethod
    def error(
        message: str = "Internal Server Error",
        status_code: int = 500,
        errors: Optional[List[Dict[str, str]]] = None
    ) -> JSONResponse:
        """Return error response"""
        response = {
            "success": False,
            "message": message,
            "errors": errors,
            "timestamp": datetime.utcnow().isoformat()
        }
        return JSONResponse(content=response, status_code=status_code)

    @staticmethod
    def validation_error(
        errors: List[Dict[str, str]]
    ) -> JSONResponse:
        """Return validation error response"""
        response = {
            "success": False,
            "message": "Validation Error",
            "errors": errors,
            "timestamp": datetime.utcnow().isoformat()
        }
        return JSONResponse(content=response, status_code=400)

    @staticmethod
    def unauthorized(
        message: str = "Unauthorized"
    ) -> JSONResponse:
        """Return unauthorized response"""
        response = {
            "success": False,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        return JSONResponse(content=response, status_code=401)

    @staticmethod
    def forbidden(
        message: str = "Forbidden"
    ) -> JSONResponse:
        """Return forbidden response"""
        response = {
            "success": False,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        return JSONResponse(content=response, status_code=403)

    @staticmethod
    def not_found(
        message: str = "Resource not found"
    ) -> JSONResponse:
        """Return not found response"""
        response = {
            "success": False,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        return JSONResponse(content=response, status_code=404)
