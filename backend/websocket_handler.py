from fastapi import WebSocket, WebSocketDisconnect, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Set, List
import json
import logging
from datetime import datetime
from database import get_db
from auth import get_current_user
from services.location_service import LocationService
from services.ride_service import RideService
from redis_client import redis_client

logger = logging.getLogger(__name__)

class ConnectionManager:
    """WebSocket connection manager for real-time updates"""
    
    def __init__(self):
        # Store active connections: {user_id: {ride_id: websocket}}
        self.active_connections: Dict[str, Dict[str, Set[WebSocket]]] = {}
        # Store ride monitoring: {ride_id: {user_id}}
        self.ride_monitors: Dict[str, Set[str]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        ride_id: str
    ):
        """Register new WebSocket connection"""
        await websocket.accept()
        
        # Initialize user dict if not exists
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
        
        # Initialize ride set if not exists
        if ride_id not in self.active_connections[user_id]:
            self.active_connections[user_id][ride_id] = set()
        
        # Add connection
        self.active_connections[user_id][ride_id].add(websocket)
        
        # Track ride monitor
        if ride_id not in self.ride_monitors:
            self.ride_monitors[ride_id] = set()
        self.ride_monitors[ride_id].add(user_id)
        
        logger.info(f"User {user_id} connected to ride {ride_id}")
        
        # Notify others
        await self.broadcast_to_ride(
            ride_id,
            {
                "type": "user_connected",
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            },
            exclude_user=user_id
        )

    def disconnect(
        self,
        user_id: str,
        ride_id: str,
        websocket: WebSocket
    ):
        """Remove WebSocket connection"""
        try:
            if user_id in self.active_connections:
                if ride_id in self.active_connections[user_id]:
                    self.active_connections[user_id][ride_id].discard(websocket)
                    
                    # Cleanup if empty
                    if not self.active_connections[user_id][ride_id]:
                        del self.active_connections[user_id][ride_id]
                    
                    if not self.active_connections[user_id]:
                        del self.active_connections[user_id]
            
            # Update ride monitors
            if ride_id in self.ride_monitors:
                self.ride_monitors[ride_id].discard(user_id)
                if not self.ride_monitors[ride_id]:
                    del self.ride_monitors[ride_id]
            
            logger.info(f"User {user_id} disconnected from ride {ride_id}")
        except Exception as e:
            logger.error(f"Disconnect error: {e}")

    async def broadcast_to_ride(
        self,
        ride_id: str,
        message: dict,
        exclude_user: str = None
    ):
        """Broadcast message to all users in a ride"""
        if ride_id not in self.ride_monitors:
            return
        
        disconnected = []
        
        for user_id in self.ride_monitors[ride_id]:
            if exclude_user and user_id == exclude_user:
                continue
            
            if user_id in self.active_connections:
                for websocket in self.active_connections[user_id].get(ride_id, set()):
                    try:
                        await websocket.send_json(message)
                    except Exception as e:
                        logger.error(f"Broadcast error: {e}")
                        disconnected.append((user_id, ride_id, websocket))
        
        # Clean up disconnected
        for user_id, rid, ws in disconnected:
            self.disconnect(user_id, rid, ws)

    async def broadcast_to_user(
        self,
        user_id: str,
        ride_id: str,
        message: dict
    ):
        """Send message to specific user in a ride"""
        if user_id not in self.active_connections:
            return
        
        if ride_id not in self.active_connections[user_id]:
            return
        
        disconnected = []
        
        for websocket in self.active_connections[user_id][ride_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Send error: {e}")
                disconnected.append((user_id, ride_id, websocket))
        
        for user_id, rid, ws in disconnected:
            self.disconnect(user_id, rid, ws)

    def get_active_users(self, ride_id: str) -> List[str]:
        """Get list of active users in a ride"""
        return list(self.ride_monitors.get(ride_id, set()))

    def get_connection_count(self, ride_id: str) -> int:
        """Get number of active connections in a ride"""
        return len(self.ride_monitors.get(ride_id, set()))

# Global connection manager
manager = ConnectionManager()

async def websocket_endpoint(
    websocket: WebSocket,
    ride_id: str,
    token: str,
    session: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for real-time location updates"""
    user_id = None
    
    try:
        # Verify token
        from helpers import Helpers
        try:
            decoded = Helpers.verify_access_token(token)
            user_id = decoded.get("user_id")
        except Exception:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            logger.warning(f"WebSocket: Invalid token")
            return
        
        if not user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Verify user is participant in ride
        from repositories.ride_repository import RideRepository
        ride = await RideRepository.find_by_id(session, ride_id)
        
        if not ride:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            logger.warning(f"WebSocket: Ride {ride_id} not found")
            return
        
        is_participant = any(
            p.user_id == user_id and p.status == "accepted"
            for p in ride.participants
        )
        
        if not is_participant:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            logger.warning(f"WebSocket: User {user_id} not participant in ride {ride_id}")
            return
        
        # Connect user
        await manager.connect(websocket, user_id, ride_id)
        
        # Send connection confirmation
        await manager.broadcast_to_user(
            user_id,
            ride_id,
            {
                "type": "connection_established",
                "user_id": user_id,
                "ride_id": ride_id,
                "active_users": manager.get_active_users(ride_id),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Listen for messages
        while True:
            data = await websocket.receive_json()
            
            message_type = data.get("type")
            
            if message_type == "location_update":
                # Handle location update
                latitude = data.get("latitude")
                longitude = data.get("longitude")
                accuracy = data.get("accuracy")
                
                if latitude is None or longitude is None:
                    await websocket.send_json({
                        "type": "error",
                        "message": "latitude and longitude required"
                    })
                    continue
                
                # Update location in database
                try:
                    location = await LocationService.update_user_location(
                        session,
                        user_id,
                        latitude,
                        longitude,
                        accuracy
                    )
                    
                    # Broadcast to ride participants
                    await manager.broadcast_to_ride(
                        ride_id,
                        {
                            "type": "location_update",
                            "user_id": user_id,
                            "latitude": latitude,
                            "longitude": longitude,
                            "accuracy": accuracy,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                    
                    # Check for drift
                    alerts = await LocationService.check_drift_alerts(session, ride_id)
                    if alerts:
                        await manager.broadcast_to_ride(
                            ride_id,
                            {
                                "type": "drift_alert",
                                "alerts": alerts,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        )
                
                except Exception as e:
                    logger.error(f"Location update error: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": "Failed to update location"
                    })
            
            elif message_type == "ping":
                # Heartbeat
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
    
    except WebSocketDisconnect:
        if user_id:
            manager.disconnect(user_id, ride_id, websocket)
            
            # Notify others
            await manager.broadcast_to_ride(
                ride_id,
                {
                    "type": "user_disconnected",
                    "user_id": user_id,
                    "active_users": manager.get_active_users(ride_id),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        logger.info(f"WebSocket disconnected: {user_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        if user_id:
            manager.disconnect(user_id, ride_id, websocket)
