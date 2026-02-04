"""
Shared pytest fixtures for the Kogna-AI test suite.

This module provides common fixtures for:
- Database connections (mocked)
- Authentication tokens
- User context
- API test client
- Sample data
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Generator, Dict, Any
from datetime import datetime, timedelta

# Set test environment variables before importing app modules
os.environ["SECRET_KEY"] = "test-secret-key-for-unit-tests-only"
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/kogna_test"
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_SERVICE_KEY"] = "test-service-key"
os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000"

from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport


# ============================================
# APP FIXTURE
# ============================================

@pytest.fixture(scope="session")
def app():
    """Create FastAPI application instance for testing."""
    from main import app as fastapi_app
    return fastapi_app


@pytest.fixture
def client(app) -> Generator:
    """Create synchronous test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client(app) -> Generator:
    """Create async test client for async endpoint testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ============================================
# DATABASE FIXTURES (MOCKED)
# ============================================

@pytest.fixture
def mock_db_connection():
    """Mock database connection for unit tests."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None
    mock_cursor.fetchall.return_value = []
    return mock_conn


@pytest.fixture
def mock_db(mock_db_connection):
    """Patch get_db dependency to use mock connection."""
    with patch("core.database.get_db") as mock_get_db:
        mock_get_db.return_value = iter([mock_db_connection])
        yield mock_db_connection


@pytest.fixture
def mock_db_context(mock_db_connection):
    """Patch get_db_context to use mock connection."""
    with patch("core.database.get_db_context") as mock_context:
        mock_context.return_value.__enter__ = Mock(return_value=mock_db_connection)
        mock_context.return_value.__exit__ = Mock(return_value=False)
        yield mock_db_connection


# ============================================
# AUTHENTICATION FIXTURES
# ============================================

@pytest.fixture
def sample_user() -> Dict[str, Any]:
    """Sample user data for testing."""
    return {
        "id": "user-123",
        "supabase_id": "supabase-user-123",
        "email": "test@example.com",
        "first_name": "Test",
        "second_name": "User",
        "organization_id": "org-123",
        "role": "member",
    }


@pytest.fixture
def sample_admin_user() -> Dict[str, Any]:
    """Sample admin user data for testing."""
    return {
        "id": "admin-123",
        "supabase_id": "supabase-admin-123",
        "email": "admin@example.com",
        "first_name": "Admin",
        "second_name": "User",
        "organization_id": "org-123",
        "role": "admin",
    }


@pytest.fixture
def access_token(sample_user) -> str:
    """Generate a valid access token for testing."""
    from core.security import create_access_token
    return create_access_token(data={
        "sub": sample_user["id"],
        "email": sample_user["email"],
        "id": sample_user["id"],
    })


@pytest.fixture
def admin_access_token(sample_admin_user) -> str:
    """Generate a valid admin access token for testing."""
    from core.security import create_access_token
    return create_access_token(data={
        "sub": sample_admin_user["id"],
        "email": sample_admin_user["email"],
        "id": sample_admin_user["id"],
    })


@pytest.fixture
def auth_headers(access_token) -> Dict[str, str]:
    """Generate authentication headers for testing."""
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_auth_headers(admin_access_token) -> Dict[str, str]:
    """Generate admin authentication headers for testing."""
    return {"Authorization": f"Bearer {admin_access_token}"}


@pytest.fixture
def expired_token() -> str:
    """Generate an expired access token for testing."""
    from jose import jwt
    from core.config import SECRET_KEY, ALGORITHM

    payload = {
        "sub": "user-123",
        "email": "test@example.com",
        "id": "user-123",
        "iat": int((datetime.utcnow() - timedelta(hours=1)).timestamp()),
        "exp": datetime.utcnow() - timedelta(minutes=30),
        "token_type": "access",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ============================================
# USER CONTEXT FIXTURES
# ============================================

@pytest.fixture
def mock_user_context():
    """Create a mock UserContext for testing."""
    from core.permissions import UserContext

    return UserContext(
        id="user-123",
        supabase_id="supabase-user-123",
        email="test@example.com",
        organization_id="org-123",
        first_name="Test",
        second_name="User",
        role_name="analyst",
        role_level=2,
        permissions=[
            "insights:read:team",
            "objectives:read:team",
            "objectives:write:own",
        ],
        team_ids=["team-1", "team-2"],
    )


@pytest.fixture
def mock_manager_context():
    """Create a mock manager UserContext for testing."""
    from core.permissions import UserContext

    return UserContext(
        id="manager-123",
        supabase_id="supabase-manager-123",
        email="manager@example.com",
        organization_id="org-123",
        first_name="Manager",
        second_name="User",
        role_name="manager",
        role_level=3,
        permissions=[
            "insights:read:organization",
            "objectives:read:organization",
            "objectives:write:team",
            "agents:invoke:team",
        ],
        team_ids=["team-1", "team-2", "team-3"],
    )


@pytest.fixture
def mock_executive_context():
    """Create a mock executive UserContext for testing."""
    from core.permissions import UserContext

    return UserContext(
        id="exec-123",
        supabase_id="supabase-exec-123",
        email="executive@example.com",
        organization_id="org-123",
        first_name="Executive",
        second_name="User",
        role_name="executive",
        role_level=4,
        permissions=[
            "insights:read:organization",
            "insights:write:organization",
            "objectives:read:organization",
            "objectives:write:organization",
            "agents:invoke:organization",
            "kpis:read:organization",
            "kpis:write:organization",
        ],
        team_ids=["team-1", "team-2", "team-3", "team-4"],
    )


# ============================================
# SAMPLE DATA FIXTURES
# ============================================

@pytest.fixture
def sample_team() -> Dict[str, Any]:
    """Sample team data for testing."""
    return {
        "id": "team-123",
        "name": "Engineering",
        "organization_id": "org-123",
        "created_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_organization() -> Dict[str, Any]:
    """Sample organization data for testing."""
    return {
        "id": "org-123",
        "name": "Test Organization",
        "industry": "Technology",
        "created_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_objective() -> Dict[str, Any]:
    """Sample objective data for testing."""
    return {
        "id": "obj-123",
        "name": "Increase Revenue",
        "description": "Increase quarterly revenue by 20%",
        "organization_id": "org-123",
        "team_responsible": "team-123",
        "status": "in_progress",
        "progress": 45.5,
        "due_date": (datetime.utcnow() + timedelta(days=90)).isoformat(),
    }


@pytest.fixture
def sample_kpi() -> Dict[str, Any]:
    """Sample KPI data for testing."""
    return {
        "id": "kpi-123",
        "name": "Monthly Revenue",
        "value": 150000.00,
        "unit": "USD",
        "trend": 5.2,
        "organization_id": "org-123",
        "team_id": "team-123",
        "period": "2024-01",
    }


@pytest.fixture
def sample_insight() -> Dict[str, Any]:
    """Sample insight data for testing."""
    return {
        "id": "insight-123",
        "title": "Revenue Growth Opportunity",
        "content": "Analysis shows potential for 15% growth in Q2",
        "category": "revenue",
        "priority": "high",
        "organization_id": "org-123",
        "created_at": datetime.utcnow().isoformat(),
    }


# ============================================
# ETL FIXTURES
# ============================================

@pytest.fixture
def sample_jira_issue() -> Dict[str, Any]:
    """Sample Jira issue data for testing."""
    return {
        "key": "PROJ-123",
        "id": "10001",
        "fields": {
            "summary": "Implement new feature",
            "description": "As a user, I want to...",
            "status": {"name": "In Progress", "id": "3"},
            "assignee": {"displayName": "John Doe", "emailAddress": "john@example.com"},
            "reporter": {"displayName": "Jane Doe", "emailAddress": "jane@example.com"},
            "priority": {"name": "High", "id": "2"},
            "issuetype": {"name": "Story", "id": "10001"},
            "project": {"key": "PROJ", "name": "Project Alpha"},
            "created": "2024-01-15T10:00:00.000+0000",
            "updated": "2024-01-16T15:30:00.000+0000",
            "sprint": {"name": "Sprint 5", "id": 100},
        }
    }


@pytest.fixture
def sample_google_drive_file() -> Dict[str, Any]:
    """Sample Google Drive file metadata for testing."""
    return {
        "id": "file-123",
        "name": "Q1 Report.docx",
        "mimeType": "application/vnd.google-apps.document",
        "createdTime": "2024-01-10T08:00:00.000Z",
        "modifiedTime": "2024-01-15T14:30:00.000Z",
        "owners": [{"displayName": "John Doe", "emailAddress": "john@example.com"}],
        "size": "15360",
    }


@pytest.fixture
def sample_connector_tokens() -> Dict[str, Any]:
    """Sample OAuth connector tokens for testing."""
    return {
        "access_token": "mock-access-token",
        "refresh_token": "mock-refresh-token",
        "token_type": "Bearer",
        "expires_in": 3600,
        "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
    }


# ============================================
# MOCK EXTERNAL SERVICES
# ============================================

@pytest.fixture
def mock_supabase():
    """Mock Supabase client for testing."""
    with patch("supabase.create_client") as mock_create:
        mock_client = MagicMock()
        mock_create.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_openai():
    """Mock OpenAI client for testing."""
    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_anthropic():
    """Mock Anthropic client for testing."""
    with patch("anthropic.Anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_httpx():
    """Mock httpx client for external API calls."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value.__aenter__ = MagicMock(return_value=mock_instance)
        mock_client.return_value.__aexit__ = MagicMock(return_value=None)
        yield mock_instance


# ============================================
# UTILITY FIXTURES
# ============================================

@pytest.fixture
def freeze_time():
    """Fixture to freeze time for testing time-sensitive code."""
    from unittest.mock import patch
    from datetime import datetime

    frozen_time = datetime(2024, 1, 15, 12, 0, 0)

    with patch("datetime.datetime") as mock_datetime:
        mock_datetime.utcnow.return_value = frozen_time
        mock_datetime.now.return_value = frozen_time
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        yield frozen_time
