from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import re

# ============================================================================
# ENUMS
# ============================================================================

class RideStatus(str, Enum):
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ParticipantStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class RideDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"

# ============================================================================
# LOCATION SCHEMAS
# ============================================================================

class LocationPoint(BaseModel):
    """Location with coordinates"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: str = Field(..., max_length=200)

class LocationUpdate(BaseModel):
    """Location update request"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy: Optional[float] = Field(None, ge=0)
    timestamp: Optional[datetime] = None

class LocationData(BaseModel):
    """Location data response"""
    id: str
    user_id: str
    latitude: float
    longitude: float
    accuracy: Optional[float]
    timestamp: datetime
    created_at: datetime

class BatchLocationUpdate(BaseModel):
    """Batch location updates"""
    locations: List[LocationUpdate] = Field(..., min_items=1)

class NearbyUserResponse(BaseModel):
    """Nearby user with distance"""
    id: str
    first_name: str
    last_name: str
    profile_picture_url: Optional[str]
    latitude: float
    longitude: float
    last_location_update: datetime
    distance_km: float

class DriftAlert(BaseModel):
    """Drift alert for ride participants"""
    user_id: str
    user_name: str
    distance_from_group: float
    max_allowed_distance: float
    latitude: float
    longitude: float
    timestamp: datetime

class LocationHistory(BaseModel):
    """Location history entry"""
    id: str
    latitude: float
    longitude: float
    accuracy: Optional[float]
    timestamp: datetime
    created_at: datetime

# ============================================================================
# USER SCHEMAS
# ============================================================================

class UserRegistrationRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    phone: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Validate password strength"""
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain lowercase letter")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain digit")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate phone number"""
        if not re.match(r"^\+?[1-9]\d{1,14}$", v):
            raise ValueError("Invalid phone number format")
        return v

class UserLoginRequest(BaseModel):
    """User login request"""
    email: EmailStr
    password: str

class UserProfileUpdate(BaseModel):
    """User profile update request"""
    first_name: Optional[str] = Field(None, min_length=2, max_length=50)
    last_name: Optional[str] = Field(None, min_length=2, max_length=50)
    phone: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    profile_picture_url: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None
    is_profile_visible: Optional[bool] = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number"""
        if v and not re.match(r"^\+?[1-9]\d{1,14}$", v):
            raise ValueError("Invalid phone number format")
        return v

class ChangePasswordRequest(BaseModel):
    """Change password request"""
    current_password: str
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Validate password strength"""
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain lowercase letter")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain digit")
        return v

class UserStats(BaseModel):
    """User statistics"""
    rides_created: int
    rides_joined: int
    completed_rides: int

class UserResponse(BaseModel):
    """User response (without sensitive data)"""
    id: str
    email: str
    first_name: str
    last_name: str
    phone: str
    bio: Optional[str]
    profile_picture_url: Optional[str]
    is_active: bool
    is_profile_visible: bool
    role: UserRole
    created_at: datetime
    updated_at: datetime
    stats: Optional[UserStats] = None

    class Config:
        from_attributes = True

class UserWithTokenResponse(BaseModel):
    """User response with authentication tokens"""
    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str

# ============================================================================
# RIDE SCHEMAS
# ============================================================================

class CreateRideRequest(BaseModel):
    """Create ride request"""
    title: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    start_location: LocationPoint
    end_location: LocationPoint
    scheduled_date_time: datetime = Field(..., alias="scheduledDateTime")
    is_public: bool = True
    max_participants: int = Field(10, ge=1, le=20)
    estimated_duration_minutes: Optional[int] = Field(None, ge=1)
    difficulty: RideDifficulty = RideDifficulty.MEDIUM

    class Config:
        populate_by_name = True

class UpdateRideRequest(BaseModel):
    """Update ride request"""
    title: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    start_location: Optional[LocationPoint] = None
    end_location: Optional[LocationPoint] = None
    scheduled_date_time: Optional[datetime] = Field(None, alias="scheduledDateTime")
    is_public: Optional[bool] = None
    max_participants: Optional[int] = Field(None, ge=1, le=20)
    estimated_duration_minutes: Optional[int] = Field(None, ge=1)
    difficulty: Optional[RideDifficulty] = None
    status: Optional[RideStatus] = None

    class Config:
        populate_by_name = True

class RideParticipant(BaseModel):
    """Ride participant info"""
    id: str
    ride_id: str
    user_id: str
    first_name: str
    last_name: str
    profile_picture_url: Optional[str]
    email: str
    status: ParticipantStatus
    joined_at: datetime

    class Config:
        from_attributes = True

class RideResponse(BaseModel):
    """Ride response"""
    id: str
    title: str
    description: Optional[str]
    start_latitude: float
    start_longitude: float
    start_address: str
    end_latitude: float
    end_longitude: float
    end_address: str
    scheduled_date_time: datetime
    status: RideStatus
    is_public: bool
    max_participants: int
    estimated_duration_minutes: Optional[int]
    difficulty: RideDifficulty
    created_by: str
    creator_first_name: Optional[str]
    creator_last_name: Optional[str]
    creator_profile_picture: Optional[str]
    created_at: datetime
    updated_at: datetime
    participants: Optional[List[RideParticipant]] = None
    participant_count: Optional[int] = 0
    distance_km: Optional[float] = None
    is_participant: Optional[bool] = None
    participant_status: Optional[ParticipantStatus] = None

    class Config:
        from_attributes = True

class SearchRidesRequest(BaseModel):
    """Search rides request"""
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    radius_km: float = Field(50, ge=0.1)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    difficulty: Optional[RideDifficulty] = None
    is_public: bool = True
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)

class InviteUsersRequest(BaseModel):
    """Invite users to ride"""
    user_ids: List[str] = Field(..., min_items=1)
    message: Optional[str] = Field(None, max_length=200)

class InvitationResponse(BaseModel):
    """Invitation response"""
    user_id: str
    status: str  # "invited", "failed"
    error: Optional[str] = None

# ============================================================================
# PAGINATION SCHEMAS
# ============================================================================

class PaginationMeta(BaseModel):
    """Pagination metadata"""
    current_page: int
    total_pages: int
    page_size: int
    total_count: int
    has_next: bool
    has_prev: bool

class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    items: List[Any]
    pagination: PaginationMeta

# ============================================================================
# GENERIC RESPONSE SCHEMAS
# ============================================================================

class SuccessResponse(BaseModel):
    """Success response wrapper"""
    success: bool = True
    message: str
    data: Optional[Any] = None
    timestamp: datetime

class ErrorDetail(BaseModel):
    """Error detail"""
    field: str
    message: str

class ErrorResponse(BaseModel):
    """Error response wrapper"""
    success: bool = False
    message: str
    errors: Optional[List[ErrorDetail]] = None
    timestamp: datetime

# ============================================================================
# SEARCH SCHEMAS
# ============================================================================

class UserSearchRequest(BaseModel):
    """Search users request"""
    q: str = Field(..., min_length=2)
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)

class UserSearchResponse(BaseModel):
    """User search response"""
    users: List[UserResponse]
    pagination: PaginationMeta
