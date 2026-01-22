import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_create_ride(async_client: AsyncClient, mock_ride_service, mocker):
    # Mock auth dependency
    # Note: We need to mock get_current_user global dependency in main app or override it
    # But since we're using unittest.mock on the SERVICE layer, the route handler will still run
    # and try to resolve dependencies.
    # So we MUST override the auth dependency in the app.
    # This is tricky with `mock_ride_service` alone.
    
    # We'll use app.dependency_overrides in the test function or fixture
    from main import app
    from auth import get_current_user
    
    mock_user = {"user_id": "test-user-id", "email": "test@example.com", "role": "user"}
    app.dependency_overrides[get_current_user] = lambda: mock_user

    mock_ride_service.create_ride.return_value = {
        "id": "ride-123",
        "title": "Test Ride",
        "start_latitude": 10.0,
        "start_longitude": 20.0,
        "created_by": "test-user-id"
    }

    payload = {
        "title": "Test Ride",
        "start_location": {"latitude": 10.0, "longitude": 20.0, "address": "Start"},
        "end_location": {"latitude": 11.0, "longitude": 21.0, "address": "End"},
        "scheduled_date_time": (datetime.utcnow() + timedelta(days=1)).isoformat()
    }

    response = await async_client.post("/api/v1/rides", json=payload)
    
    # Reset override
    app.dependency_overrides = {}

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == "ride-123"

@pytest.mark.asyncio
async def test_get_ride_details(async_client: AsyncClient, mock_ride_service):
    # Mock auth
    from main import app
    from auth import get_current_user
    mock_user = {"user_id": "test-user-id", "role": "user"}
    app.dependency_overrides[get_current_user] = lambda: mock_user

    mock_ride_service.get_ride_details.return_value = {
        "id": "ride-123",
        "title": "Test Ride"
    }

    response = await async_client.get("/api/v1/rides/ride-123")
    
    app.dependency_overrides = {}

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["title"] == "Test Ride"
