from datetime import datetime
from collections import defaultdict
from logger import logger, error as log_error
from routing_service import RoutingService
import asyncio

# In-memory storage of active rides
active_rides = {}

def initialize_socket_handler(sio):
    """Initialize Socket.IO event handlers"""
    
    @sio.event
    async def connect(sid, environ):
        logger.info(f'✅ User connected: {sid}')
    
    @sio.event
    async def join_ride(sid, data):
        """Handle user joining a ride"""
        try:
            ride_id = data.get('rideId')
            user_id = data.get('userId')
            username = data.get('username')
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            
            # Join Socket.IO room
            await sio.enter_room(sid, f'ride_{ride_id}')
            
            # Initialize ride if not exists
            if ride_id not in active_rides:
                active_rides[ride_id] = {'participants': {}}
            
            ride = active_rides[ride_id]
            ride['participants'][user_id] = {
                'userId': user_id,
                'username': username,
                'latitude': latitude,
                'longitude': longitude,
                'lastUpdate': datetime.now().isoformat(),
                'socketId': sid
            }
            
            participants = list(ride['participants'].values())
            
            # Broadcast to all users in ride
            await sio.emit('participant_joined', {
                'userId': user_id,
                'username': username,
                'latitude': latitude,
                'longitude': longitude,
                'totalParticipants': len(participants)
            }, room=f'ride_{ride_id}')
            
            logger.info(f'👤 {username} joined ride {ride_id}. Total: {len(participants)}')
            
        except Exception as error:
            log_error(f'Error joining ride: {str(error)}')
    
    @sio.event
    async def location_update(sid, data):
        """Handle location update"""
        try:
            ride_id = data.get('rideId')
            user_id = data.get('userId')
            username = data.get('username')
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            
            if ride_id not in active_rides:
                return
            
            ride = active_rides[ride_id]
            
            if user_id in ride['participants']:
                ride['participants'][user_id] = {
                    'userId': user_id,
                    'username': username,
                    'latitude': latitude,
                    'longitude': longitude,
                    'lastUpdate': datetime.now().isoformat(),
                    'socketId': ride['participants'][user_id].get('socketId')
                }
                
                await sio.emit('rider_location_update', {
                    'userId': user_id,
                    'username': username,
                    'latitude': latitude,
                    'longitude': longitude,
                    'timestamp': datetime.now().isoformat()
                }, room=f'ride_{ride_id}')
        
        except Exception as error:
            log_error(f'Error updating location: {str(error)}')
    
    @sio.event
    async def leave_ride(sid, data):
        """Handle user leaving a ride"""
        try:
            ride_id = data.get('rideId')
            user_id = data.get('userId')
            username = data.get('username')
            
            if ride_id in active_rides:
                ride = active_rides[ride_id]
                
                if user_id in ride['participants']:
                    del ride['participants'][user_id]
                
                await sio.emit('participant_left', {
                    'userId': user_id,
                    'username': username,
                    'totalParticipants': len(ride['participants'])
                }, room=f'ride_{ride_id}')
                
                # Remove ride if no participants
                if len(ride['participants']) == 0:
                    del active_rides[ride_id]
            
            await sio.leave_room(sid, f'ride_{ride_id}')
        
        except Exception as error:
            log_error(f'Error leaving ride: {str(error)}')
    
    @sio.event
    async def get_ride_status(sid, data):
        """Get current ride status"""
        ride_id = data.get('rideId')
        
        if ride_id in active_rides:
            ride = active_rides[ride_id]
            participants = list(ride['participants'].values())
            await sio.emit('ride_status', {
                'rideId': ride_id,
                'participants': participants,
                'totalParticipants': len(participants)
            }, to=sid)
        else:
            await sio.emit('ride_status', {
                'rideId': ride_id,
                'participants': [],
                'totalParticipants': 0
            }, to=sid)
    
    @sio.event
    async def get_route(sid, data, callback):
        """Get route polyline from start to end"""
        try:
            start_lat = data.get('startLat')
            start_lon = data.get('startLon')
            end_lat = data.get('endLat')
            end_lon = data.get('endLon')
            
            route = await RoutingService.get_route(start_lat, start_lon, end_lat, end_lon)
            callback(route)
        
        except Exception as error:
            callback({'success': False, 'error': str(error)})
    
    @sio.event
    async def disconnect(sid):
        """Handle user disconnect"""
        logger.info(f'❌ User disconnected: {sid}')
        
        # Find and clean up user from all rides
        for ride_id in list(active_rides.keys()):
            ride = active_rides[ride_id]
            user_to_remove = None
            
            for user_id, participant in ride['participants'].items():
                if participant.get('socketId') == sid:
                    user_to_remove = user_id
                    break
            
            if user_to_remove:
                participant = ride['participants'][user_to_remove]
                del ride['participants'][user_to_remove]
                
                await sio.emit('participant_left', {
                    'userId': user_to_remove,
                    'username': participant['username'],
                    'totalParticipants': len(ride['participants'])
                }, room=f'ride_{ride_id}')
                
                # Remove ride if empty
                if len(ride['participants']) == 0:
                    del active_rides[ride_id]
