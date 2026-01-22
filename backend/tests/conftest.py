import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from main import app
from unittest.mock import MagicMock

# Event loop fixture
@pytest.fixture(scope="session")
def event_loop() -> Generator:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

# AsyncClient fixture for testing endpoints
@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

# Mocks for services will be handled in individual test files or here if shared
@pytest.fixture
def mock_user_service(mocker):
    return mocker.patch("routes.auth_routes.UserService")

@pytest.fixture
def mock_ride_service(mocker):
    return mocker.patch("routes.ride_routes.RideService")
