from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
from config import settings
import logging

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)

def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded"""
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "message": "Too many requests. Please try again later.",
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }
    )

# Rate limit decorators
AUTH_LIMITER = f"{settings.auth_rate_limit_max_requests}/15minute"
LOCATION_LIMITER = f"{settings.location_rate_limit_max_requests}/minute"
GENERAL_LIMITER = f"{settings.rate_limit_max_requests}/{settings.rate_limit_window_minutes}minute"
