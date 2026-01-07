from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import uvicorn
import os

from config import settings
from logger import setup_logger
from redis_client import redis_client
from database import async_engine, Base
from error_handler import install_exception_handlers
from rate_limiter import limiter, rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Import route modules
from routes import auth_routes, user_routes, ride_routes, location_routes

# Setup logger
logger = setup_logger()

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for startup and shutdown"""
    # Startup
    logger.info("Starting up application...")
    try:
        await redis_client.connect()
        logger.info("Redis connected successfully")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
    
    # Create database tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await redis_client.disconnect()
    await async_engine.dispose()
    logger.info("Application shutdown complete")

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"/openapi.json",
    lifespan=lifespan
)

# Add exception handlers
install_exception_handlers(app)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Trusted Host Middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1"]  # Add your hosts
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    logger.info(f"{request.method} {request.url.path}")
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Request error: {e}", exc_info=True)
        raise

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "environment": settings.environment,
        "redis_connected": redis_client.is_connected
    }

# Root endpoint
@app.get("/", tags=["Info"])
async def root():
    """API root endpoint"""
    return {
        "message": "Welcome to RideShare API",
        "version": settings.api_version,
        "docs": "/docs",
        "redoc": "/redoc"
    }

# Include route modules
app.include_router(auth_routes.router)
app.include_router(user_routes.router)
app.include_router(ride_routes.router)
app.include_router(location_routes.router)

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "message": f"Route {request.url.path} not found",
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )
