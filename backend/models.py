from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, 
    ForeignKey, Enum, JSON, Text, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
import uuid
from datetime import datetime
from database import Base
from schemas import RideStatus, ParticipantStatus, RideDifficulty, UserRole

# ============================================================================
# USER MODEL
# ============================================================================

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint('email', name='uq_users_email'),
        Index('idx_users_email', 'email'),
        Index('idx_users_is_active', 'is_active'),
        Index('idx_users_is_profile_visible', 'is_profile_visible'),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=False)
    bio = Column(Text, nullable=True)
    profile_picture_url = Column(String(500), nullable=True)
    social_links = Column(JSON, nullable=True, default={})
    is_active = Column(Boolean, default=True)
    is_profile_visible = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.USER)
    refresh_token = Column(String(500), nullable=True)
    current_latitude = Column(Float, nullable=True)
    current_longitude = Column(Float, nullable=True)
    last_location_update = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    rides_created = relationship("Ride", back_populates="creator", foreign_keys="Ride.created_by")
    ride_participants = relationship("RideParticipant", back_populates="user")
    locations = relationship("LocationUpdate", back_populates="user")
    drift_alerts = relationship("DriftAlert", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"

# ============================================================================
# RIDE MODEL
# ============================================================================

class Ride(Base):
    __tablename__ = "rides"
    __table_args__ = (
        Index('idx_rides_created_by', 'created_by'),
        Index('idx_rides_status', 'status'),
        Index('idx_rides_is_public', 'is_public'),
        Index('idx_rides_scheduled_date_time', 'scheduled_date_time'),
        Index('idx_rides_start_location', 'start_latitude', 'start_longitude'),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    start_latitude = Column(Float, nullable=False)
    start_longitude = Column(Float, nullable=False)
    start_address = Column(String(200), nullable=False)
    end_latitude = Column(Float, nullable=False)
    end_longitude = Column(Float, nullable=False)
    end_address = Column(String(200), nullable=False)
    scheduled_date_time = Column(DateTime, nullable=False)
    status = Column(Enum(RideStatus), default=RideStatus.SCHEDULED)
    is_public = Column(Boolean, default=True)
    max_participants = Column(Integer, default=10)
    estimated_duration_minutes = Column(Integer, nullable=True)
    difficulty = Column(Enum(RideDifficulty), default=RideDifficulty.MEDIUM)
    created_by = Column(String(36), ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    creator = relationship("User", back_populates="rides_created", foreign_keys=[created_by])
    participants = relationship("RideParticipant", back_populates="ride", cascade="all, delete-orphan")
    drift_alerts = relationship("DriftAlert", back_populates="ride", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Ride(id={self.id}, title={self.title})>"

# ============================================================================
# RIDE PARTICIPANT MODEL
# ============================================================================

class RideParticipant(Base):
    __tablename__ = "ride_participants"
    __table_args__ = (
        UniqueConstraint('ride_id', 'user_id', name='uq_ride_participants_ride_user'),
        Index('idx_ride_participants_ride_id', 'ride_id'),
        Index('idx_ride_participants_user_id', 'user_id'),
        Index('idx_ride_participants_status', 'status'),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ride_id = Column(String(36), ForeignKey('rides.id'), nullable=False)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    status = Column(Enum(ParticipantStatus), default=ParticipantStatus.PENDING)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    ride = relationship("Ride", back_populates="participants")
    user = relationship("User", back_populates="ride_participants")

    def __repr__(self):
        return f"<RideParticipant(ride_id={self.ride_id}, user_id={self.user_id})>"

# ============================================================================
# LOCATION UPDATE MODEL
# ============================================================================

class LocationUpdate(Base):
    __tablename__ = "location_updates"
    __table_args__ = (
        Index('idx_location_updates_user_id', 'user_id'),
        Index('idx_location_updates_timestamp', 'timestamp'),
        Index('idx_location_updates_created_at', 'created_at'),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    accuracy = Column(Float, nullable=True)
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="locations")

    def __repr__(self):
        return f"<LocationUpdate(user_id={self.user_id}, timestamp={self.timestamp})>"

# ============================================================================
# DRIFT ALERT MODEL
# ============================================================================

class DriftAlert(Base):
    __tablename__ = "drift_alerts"
    __table_args__ = (
        Index('idx_drift_alerts_ride_id', 'ride_id'),
        Index('idx_drift_alerts_user_id', 'user_id'),
        Index('idx_drift_alerts_created_at', 'created_at'),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ride_id = Column(String(36), ForeignKey('rides.id'), nullable=False)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    distance = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    ride = relationship("Ride", back_populates="drift_alerts")
    user = relationship("User", back_populates="drift_alerts")

    def __repr__(self):
        return f"<DriftAlert(ride_id={self.ride_id}, user_id={self.user_id})>"
