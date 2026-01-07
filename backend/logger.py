import logging
import logging.handlers
import os
from config import settings
from datetime import datetime

def setup_logger(name: str = "rideshare") -> logging.Logger:
    """Setup logger with file and console handlers"""
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level))
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(settings.log_file) or ".", exist_ok=True)
    
    # Log format
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler (rotating)
    file_handler = logging.handlers.RotatingFileHandler(
        filename=settings.log_file,
        maxBytes=5242880,  # 5MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    
    # Error file handler
    error_file_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(os.path.dirname(settings.log_file) or ".", "error.log"),
        maxBytes=5242880,
        backupCount=5
    )
    error_file_handler.setFormatter(formatter)
    error_file_handler.setLevel(logging.ERROR)
    logger.addHandler(error_file_handler)
    
    # Console handler (only in development)
    if settings.environment != "production":
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(getattr(logging, settings.log_level))
        logger.addHandler(console_handler)
    
    return logger

logger = setup_logger()
