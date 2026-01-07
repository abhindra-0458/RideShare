import os
from dotenv import load_dotenv

load_dotenv()

# Server
PORT = int(os.getenv('PORT', 3000))
NODE_ENV = os.getenv('NODE_ENV', 'development')
API_VERSION = os.getenv('API_VERSION', 'v1')

# Database (merged from config.js + index.js)
DATABASE = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'name': os.getenv('DB_NAME', 'rideshare_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '820958'),
    'url': os.getenv('DATABASE_URL'),
}

# JWT
JWT = {
    'secret': os.getenv('JWT_SECRET'),
    'refresh_secret': os.getenv('JWT_REFRESH_SECRET'),
    'expires_in': os.getenv('JWT_EXPIRE', '15m'),
    'refresh_expires_in': os.getenv('JWT_REFRESH_EXPIRE', '7d'),
}

# Redis
REDIS = {
    'url': os.getenv('REDIS_URL', 'redis://localhost:6379'),
    'password': os.getenv('REDIS_PASSWORD'),
}

# Upload
UPLOAD = {
    'path': os.getenv('UPLOAD_PATH', 'uploads/'),
    'max_file_size': int(os.getenv('MAX_FILE_SIZE', 5242880)),  # 5MB
    'allowed_types': os.getenv('ALLOWED_FILE_TYPES', 'jpg,jpeg,png,gif').split(','),
}

# Rate Limit
RATE_LIMIT = {
    'window_ms': int(os.getenv('RATE_LIMIT_WINDOW_MS', 900000)),  # 15 minutes
    'max_requests': int(os.getenv('RATE_LIMIT_MAX_REQUESTS', 100)),
}

# Location
LOCATION = {
    'drift_alert_distance_km': float(os.getenv('DRIFT_ALERT_DISTANCE_KM', 2)),
    'update_interval_ms': int(os.getenv('LOCATION_UPDATE_INTERVAL_MS', 30000)),
}

# WebSocket
WEBSOCKET = {
    'cors_origin': os.getenv('WEBSOCKET_CORS_ORIGIN', 'http://localhost:3000'),
}

# Logging
LOGGING = {
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'file': os.getenv('LOG_FILE', 'logs/app.log'),
}
