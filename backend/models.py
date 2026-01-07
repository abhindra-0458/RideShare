from datetime import datetime
from typing import List, Optional
from uuid import UUID

class User:
    """User model - in-memory representation"""
    def __init__(self, id: str, username: str, latitude: float, longitude: float):
        self.id = id
        self.username = username
        self.latitude = latitude
        self.longitude = longitude
        self.created_at = datetime.now()

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'created_at': self.created_at.isoformat()
        }


class Location:
    """Location model - in-memory representation"""
    def __init__(self, user_id: str, username: str, latitude: float, longitude: float):
        self.user_id = user_id
        self.username = username
        self.latitude = latitude
        self.longitude = longitude
        self.timestamp = datetime.now()

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'timestamp': self.timestamp.isoformat()
        }


class Ride:
    """Ride model - in-memory representation"""
    def __init__(self, id: str, title: str, destination: str, created_by: str):
        self.id = id
        self.title = title
        self.destination = destination
        self.created_by = created_by
        self.status = 'active'
        self.participants: List[dict] = []
        self.created_at = datetime.now()

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'destination': self.destination,
            'created_by': self.created_by,
            'status': self.status,
            'participants': self.participants,
            'created_at': self.created_at.isoformat()
        }
