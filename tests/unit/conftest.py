import pytest
from unittest.mock import AsyncMock


@pytest.fixture
def mock_user_repo():
    mock = AsyncMock()
    mock.get_by_email = AsyncMock()
    mock.get_by_id = AsyncMock()
    mock.create = AsyncMock()
    mock.search_in_org = AsyncMock()
    return mock


@pytest.fixture
def mock_org_repo():
    mock = AsyncMock()
    mock.create = AsyncMock()
    mock.get_by_id = AsyncMock()
    return mock


@pytest.fixture
def mock_membership_repo():
    mock = AsyncMock()
    mock.create = AsyncMock()
    mock.get = AsyncMock()
    mock.get_users_in_org = AsyncMock()
    return mock


@pytest.fixture
def mock_item_repo():
    mock = AsyncMock()
    mock.create = AsyncMock()
    mock.get_by_org = AsyncMock()
    return mock


@pytest.fixture
def mock_audit_repo():
    mock = AsyncMock()
    mock.create = AsyncMock()
    mock.get_by_org = AsyncMock()
    mock.get_today_by_org = AsyncMock()
    return mock
