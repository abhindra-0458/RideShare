import pytest
from httpx import AsyncClient
from schemas import UserRegistrationRequest

@pytest.mark.asyncio
async def test_register_user_success(async_client: AsyncClient, mock_user_service):
    # Setup mock
    mock_user_service.register_user.return_value = {
        "id": "test-uuid",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User"
    }

    payload = {
        "email": "test@example.com",
        "password": "Password123!",
        "first_name": "Test",
        "last_name": "User",
        "phone": "+1234567890"
    }

    response = await async_client.post("/api/v1/auth/register", json=payload)

    if response.status_code != 201:
        print(f"FAILED: {response.status_code} {response.text}")

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == "test@example.com"
    mock_user_service.register_user.assert_called_once()

@pytest.mark.asyncio
async def test_login_user_success(async_client: AsyncClient, mock_user_service):
    # Setup mock
    mock_user_service.login_user.return_value = {
        "access_token": "valid_token",
        "refresh_token": "valid_refresh",
        "token_type": "bearer",
        "user": {
            "id": "test-uuid",
            "email": "test@example.com"
        }
    }

    payload = {
        "email": "test@example.com",
        "password": "Password123!"
    }

    response = await async_client.post("/api/v1/auth/login", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["access_token"] == "valid_token"
    mock_user_service.login_user.assert_called_once()
