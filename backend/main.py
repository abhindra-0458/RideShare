from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import socketio
from datetime import datetime

from config import PORT, WEBSOCKET
from logger import logger
from database import database
from socket_handler import initialize_socket_handler
from redis_client import redis_client

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    ping_timeout=60,
    ping_interval=25
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    database.initialize()
    try:
        await redis_client.connect()
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        # continue without Redis

    logger.info(f'🚀 Server running on port {PORT}')
    yield
    try:
        await redis_client.disconnect()
    except Exception:
        pass

app = FastAPI(title='RideShare Backend', lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Mount Socket.IO
app.mount('/socket.io', socketio.ASGIApp(sio))

# Initialize Socket.IO handlers
initialize_socket_handler(sio)

@app.get('/health')
async def health():
    """Health check endpoint"""
    return {
        'status': 'Backend running',
        'timestamp': datetime.now().isoformat()
    }

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=PORT)


# start redis before app docker run -p 6379:6379 redis:latest then uvicorn main:app --reload