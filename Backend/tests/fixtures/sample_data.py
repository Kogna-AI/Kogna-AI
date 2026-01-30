"""
Static sample data for testing.

This module provides pre-defined test data that represents realistic
scenarios for the Kogna-AI application. Use this data for tests that
need consistent, predictable values.

For dynamic test data generation, use the factories in factories.py.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any


# ============================================
# TIMESTAMPS
# ============================================

# Fixed timestamp for consistent testing
TEST_TIMESTAMP = "2024-01-15T12:00:00Z"
TEST_DATETIME = datetime(2024, 1, 15, 12, 0, 0)


# ============================================
# SAMPLE USERS
# ============================================

SAMPLE_USERS: List[Dict[str, Any]] = [
    {
        "id": "user-001",
        "supabase_id": "supabase-001",
        "email": "john.doe@example.com",
        "first_name": "John",
        "second_name": "Doe",
        "organization_id": "org-001",
        "role": "member",
        "created_at": TEST_TIMESTAMP,
    },
    {
        "id": "user-002",
        "supabase_id": "supabase-002",
        "email": "jane.smith@example.com",
        "first_name": "Jane",
        "second_name": "Smith",
        "organization_id": "org-001",
        "role": "manager",
        "created_at": TEST_TIMESTAMP,
    },
    {
        "id": "user-003",
        "supabase_id": "supabase-003",
        "email": "bob.wilson@example.com",
        "first_name": "Bob",
        "second_name": "Wilson",
        "organization_id": "org-001",
        "role": "analyst",
        "created_at": TEST_TIMESTAMP,
    },
]

SAMPLE_ADMIN_USER: Dict[str, Any] = {
    "id": "admin-001",
    "supabase_id": "supabase-admin-001",
    "email": "admin@example.com",
    "first_name": "System",
    "second_name": "Administrator",
    "organization_id": "org-001",
    "role": "admin",
    "created_at": TEST_TIMESTAMP,
}


# ============================================
# SAMPLE ORGANIZATION & TEAMS
# ============================================

SAMPLE_ORGANIZATION: Dict[str, Any] = {
    "id": "org-001",
    "name": "Acme Corporation",
    "industry": "Technology",
    "size": "enterprise",
    "created_at": TEST_TIMESTAMP,
}

SAMPLE_TEAMS: List[Dict[str, Any]] = [
    {
        "id": "team-001",
        "name": "Engineering",
        "organization_id": "org-001",
        "description": "Software development team",
        "created_at": TEST_TIMESTAMP,
    },
    {
        "id": "team-002",
        "name": "Product",
        "organization_id": "org-001",
        "description": "Product management team",
        "created_at": TEST_TIMESTAMP,
    },
    {
        "id": "team-003",
        "name": "Sales",
        "organization_id": "org-001",
        "description": "Sales and business development",
        "created_at": TEST_TIMESTAMP,
    },
]

SAMPLE_TEAM_MEMBERS: List[Dict[str, Any]] = [
    {
        "id": "tm-001",
        "team_id": "team-001",
        "user_id": "user-001",
        "role": "lead",
        "performance": 85.5,
        "capacity": 90.0,
        "joined_at": TEST_TIMESTAMP,
    },
    {
        "id": "tm-002",
        "team_id": "team-001",
        "user_id": "user-003",
        "role": "member",
        "performance": 78.0,
        "capacity": 100.0,
        "joined_at": TEST_TIMESTAMP,
    },
    {
        "id": "tm-003",
        "team_id": "team-002",
        "user_id": "user-002",
        "role": "manager",
        "performance": 92.0,
        "capacity": 80.0,
        "joined_at": TEST_TIMESTAMP,
    },
]


# ============================================
# SAMPLE OBJECTIVES
# ============================================

SAMPLE_OBJECTIVES: List[Dict[str, Any]] = [
    {
        "id": "obj-001",
        "name": "Increase Q1 Revenue by 20%",
        "description": "Drive revenue growth through new customer acquisition and upselling",
        "organization_id": "org-001",
        "team_responsible": "team-003",
        "status": "in_progress",
        "progress": 45.5,
        "due_date": "2024-03-31",
        "created_at": TEST_TIMESTAMP,
    },
    {
        "id": "obj-002",
        "name": "Launch New Product Feature",
        "description": "Complete development and launch of AI assistant feature",
        "organization_id": "org-001",
        "team_responsible": "team-001",
        "status": "on_track",
        "progress": 72.0,
        "due_date": "2024-02-28",
        "created_at": TEST_TIMESTAMP,
    },
    {
        "id": "obj-003",
        "name": "Improve Customer Satisfaction",
        "description": "Achieve NPS score of 50+ through improved support",
        "organization_id": "org-001",
        "team_responsible": "team-002",
        "status": "at_risk",
        "progress": 30.0,
        "due_date": "2024-06-30",
        "created_at": TEST_TIMESTAMP,
    },
]


# ============================================
# SAMPLE KPIS
# ============================================

SAMPLE_KPIS: List[Dict[str, Any]] = [
    {
        "id": "kpi-001",
        "name": "Monthly Revenue",
        "value": 150000.00,
        "unit": "USD",
        "trend": 5.2,
        "trend_direction": "up",
        "organization_id": "org-001",
        "team_id": "team-003",
        "period": "2024-01",
        "created_at": TEST_TIMESTAMP,
    },
    {
        "id": "kpi-002",
        "name": "Active Users",
        "value": 5000,
        "unit": "count",
        "trend": 12.1,
        "trend_direction": "up",
        "organization_id": "org-001",
        "team_id": None,
        "period": "2024-01",
        "created_at": TEST_TIMESTAMP,
    },
    {
        "id": "kpi-003",
        "name": "Customer Satisfaction",
        "value": 4.5,
        "unit": "rating",
        "trend": 2.3,
        "trend_direction": "up",
        "organization_id": "org-001",
        "team_id": "team-002",
        "period": "2024-01",
        "created_at": TEST_TIMESTAMP,
    },
    {
        "id": "kpi-004",
        "name": "Sprint Velocity",
        "value": 42,
        "unit": "points",
        "trend": -3.5,
        "trend_direction": "down",
        "organization_id": "org-001",
        "team_id": "team-001",
        "period": "2024-01",
        "created_at": TEST_TIMESTAMP,
    },
    {
        "id": "kpi-005",
        "name": "Bug Resolution Time",
        "value": 2.5,
        "unit": "days",
        "trend": -15.0,
        "trend_direction": "down",  # Lower is better
        "organization_id": "org-001",
        "team_id": "team-001",
        "period": "2024-01",
        "created_at": TEST_TIMESTAMP,
    },
]


# ============================================
# SAMPLE INSIGHTS
# ============================================

SAMPLE_INSIGHTS: List[Dict[str, Any]] = [
    {
        "id": "insight-001",
        "title": "Revenue Growth Opportunity Identified",
        "content": "Analysis shows potential for 15% additional growth in Q2 by focusing on enterprise segment.",
        "category": "revenue",
        "priority": "high",
        "organization_id": "org-001",
        "source": "ai_analysis",
        "created_at": TEST_TIMESTAMP,
    },
    {
        "id": "insight-002",
        "title": "Team Velocity Improvement",
        "content": "Sprint velocity has increased by 20% over the last 3 sprints following process improvements.",
        "category": "performance",
        "priority": "medium",
        "organization_id": "org-001",
        "source": "jira",
        "created_at": TEST_TIMESTAMP,
    },
    {
        "id": "insight-003",
        "title": "Customer Churn Risk Alert",
        "content": "3 enterprise customers showing decreased engagement patterns that historically precede churn.",
        "category": "risk",
        "priority": "critical",
        "organization_id": "org-001",
        "source": "ai_analysis",
        "created_at": TEST_TIMESTAMP,
    },
]


# ============================================
# SAMPLE ETL DATA
# ============================================

SAMPLE_JIRA_ISSUES: List[Dict[str, Any]] = [
    {
        "key": "PROJ-101",
        "id": "10001",
        "fields": {
            "summary": "Implement user authentication",
            "description": "Add OAuth2 authentication flow for user login",
            "status": {"name": "Done", "id": "3"},
            "assignee": {"displayName": "John Doe", "emailAddress": "john@example.com"},
            "reporter": {"displayName": "Jane Smith", "emailAddress": "jane@example.com"},
            "priority": {"name": "High", "id": "2"},
            "issuetype": {"name": "Story", "id": "10001"},
            "project": {"key": "PROJ", "name": "Main Project"},
            "created": "2024-01-10T10:00:00.000+0000",
            "updated": "2024-01-15T15:30:00.000+0000",
            "sprint": {"name": "Sprint 5", "id": 100},
            "storyPoints": 8,
        },
    },
    {
        "key": "PROJ-102",
        "id": "10002",
        "fields": {
            "summary": "Fix dashboard loading performance",
            "description": "Optimize API calls to improve dashboard load time",
            "status": {"name": "In Progress", "id": "2"},
            "assignee": {"displayName": "Bob Wilson", "emailAddress": "bob@example.com"},
            "reporter": {"displayName": "John Doe", "emailAddress": "john@example.com"},
            "priority": {"name": "Critical", "id": "1"},
            "issuetype": {"name": "Bug", "id": "10002"},
            "project": {"key": "PROJ", "name": "Main Project"},
            "created": "2024-01-12T09:00:00.000+0000",
            "updated": "2024-01-15T11:00:00.000+0000",
            "sprint": {"name": "Sprint 5", "id": 100},
            "storyPoints": 5,
        },
    },
    {
        "key": "PROJ-103",
        "id": "10003",
        "fields": {
            "summary": "Add export to CSV feature",
            "description": "Allow users to export KPI data to CSV format",
            "status": {"name": "To Do", "id": "1"},
            "assignee": None,
            "reporter": {"displayName": "Jane Smith", "emailAddress": "jane@example.com"},
            "priority": {"name": "Medium", "id": "3"},
            "issuetype": {"name": "Story", "id": "10001"},
            "project": {"key": "PROJ", "name": "Main Project"},
            "created": "2024-01-14T14:00:00.000+0000",
            "updated": "2024-01-14T14:00:00.000+0000",
            "sprint": None,
            "storyPoints": 3,
        },
    },
]

SAMPLE_GOOGLE_DRIVE_FILES: List[Dict[str, Any]] = [
    {
        "id": "gdrive-001",
        "name": "Q1 2024 Strategy.docx",
        "mimeType": "application/vnd.google-apps.document",
        "createdTime": "2024-01-05T09:00:00.000Z",
        "modifiedTime": "2024-01-15T10:30:00.000Z",
        "owners": [{"displayName": "Jane Smith", "emailAddress": "jane@example.com"}],
        "size": "25600",
        "webViewLink": "https://docs.google.com/document/d/gdrive-001/view",
    },
    {
        "id": "gdrive-002",
        "name": "Sales Report January.xlsx",
        "mimeType": "application/vnd.google-apps.spreadsheet",
        "createdTime": "2024-01-01T08:00:00.000Z",
        "modifiedTime": "2024-01-14T16:45:00.000Z",
        "owners": [{"displayName": "Sales Team", "emailAddress": "sales@example.com"}],
        "size": "102400",
        "webViewLink": "https://docs.google.com/spreadsheets/d/gdrive-002/view",
    },
]

SAMPLE_CONNECTORS: List[Dict[str, Any]] = [
    {
        "id": "conn-001",
        "type": "jira",
        "name": "Jira Cloud",
        "status": "connected",
        "organization_id": "org-001",
        "last_sync": "2024-01-15T12:00:00Z",
        "config": {
            "cloud_id": "jira-cloud-123",
            "site_url": "https://acme.atlassian.net",
        },
    },
    {
        "id": "conn-002",
        "type": "google_drive",
        "name": "Google Drive",
        "status": "connected",
        "organization_id": "org-001",
        "last_sync": "2024-01-15T11:30:00Z",
        "config": {
            "folder_id": "root",
        },
    },
    {
        "id": "conn-003",
        "type": "microsoft_teams",
        "name": "Microsoft Teams",
        "status": "disconnected",
        "organization_id": "org-001",
        "last_sync": None,
        "config": {},
    },
]


# ============================================
# SAMPLE CHAT DATA
# ============================================

SAMPLE_CONVERSATIONS: List[Dict[str, Any]] = [
    {
        "id": "conv-001",
        "user_id": "user-001",
        "title": "Revenue Analysis Q1",
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
    },
    {
        "id": "conv-002",
        "user_id": "user-001",
        "title": "Team Performance Review",
        "created_at": "2024-01-14T09:00:00Z",
        "updated_at": "2024-01-14T09:45:00Z",
    },
]

SAMPLE_MESSAGES: List[Dict[str, Any]] = [
    {
        "id": "msg-001",
        "conversation_id": "conv-001",
        "role": "user",
        "content": "What was our revenue performance last month?",
        "created_at": "2024-01-15T10:00:00Z",
    },
    {
        "id": "msg-002",
        "conversation_id": "conv-001",
        "role": "assistant",
        "content": "Based on the data, your revenue for January 2024 was $150,000, showing a 5.2% increase compared to the previous month.",
        "created_at": "2024-01-15T10:00:05Z",
    },
    {
        "id": "msg-003",
        "conversation_id": "conv-001",
        "role": "user",
        "content": "What are the main drivers of this growth?",
        "created_at": "2024-01-15T10:15:00Z",
    },
    {
        "id": "msg-004",
        "conversation_id": "conv-001",
        "role": "assistant",
        "content": "The main drivers of revenue growth were: 1) Increased enterprise customer acquisition (3 new clients), 2) Successful upselling to existing customers, and 3) Reduced churn rate from 5% to 3%.",
        "created_at": "2024-01-15T10:15:08Z",
    },
]


# ============================================
# SAMPLE API RESPONSES
# ============================================

SAMPLE_KPI_DASHBOARD_RESPONSE: Dict[str, Any] = {
    "kpis": SAMPLE_KPIS,
    "summary": {
        "total_kpis": len(SAMPLE_KPIS),
        "positive_trends": 3,
        "negative_trends": 2,
        "period": "2024-01",
    },
    "last_updated": TEST_TIMESTAMP,
}

SAMPLE_INSIGHTS_RESPONSE: Dict[str, Any] = {
    "insights": SAMPLE_INSIGHTS,
    "total": len(SAMPLE_INSIGHTS),
    "filters": {
        "category": None,
        "priority": None,
        "date_range": None,
    },
}


# ============================================
# SAMPLE ERROR RESPONSES
# ============================================

SAMPLE_ERROR_RESPONSES: Dict[str, Dict[str, Any]] = {
    "unauthorized": {
        "status_code": 401,
        "body": {"detail": "Could not validate credentials"},
    },
    "forbidden": {
        "status_code": 403,
        "body": {"detail": "Not enough permissions to perform this action"},
    },
    "not_found": {
        "status_code": 404,
        "body": {"detail": "Resource not found"},
    },
    "validation_error": {
        "status_code": 422,
        "body": {
            "detail": [
                {
                    "loc": ["body", "email"],
                    "msg": "field required",
                    "type": "value_error.missing",
                }
            ]
        },
    },
    "internal_error": {
        "status_code": 500,
        "body": {"detail": "Internal server error"},
    },
    "rate_limited": {
        "status_code": 429,
        "body": {"detail": "Too many requests. Please try again later."},
    },
}


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_user_by_id(user_id: str) -> Dict[str, Any] | None:
    """Get a sample user by ID."""
    for user in SAMPLE_USERS:
        if user["id"] == user_id:
            return user.copy()
    if SAMPLE_ADMIN_USER["id"] == user_id:
        return SAMPLE_ADMIN_USER.copy()
    return None


def get_team_by_id(team_id: str) -> Dict[str, Any] | None:
    """Get a sample team by ID."""
    for team in SAMPLE_TEAMS:
        if team["id"] == team_id:
            return team.copy()
    return None


def get_kpi_by_id(kpi_id: str) -> Dict[str, Any] | None:
    """Get a sample KPI by ID."""
    for kpi in SAMPLE_KPIS:
        if kpi["id"] == kpi_id:
            return kpi.copy()
    return None


def get_objective_by_id(objective_id: str) -> Dict[str, Any] | None:
    """Get a sample objective by ID."""
    for obj in SAMPLE_OBJECTIVES:
        if obj["id"] == objective_id:
            return obj.copy()
    return None


def get_connector_by_type(connector_type: str) -> Dict[str, Any] | None:
    """Get a sample connector by type."""
    for connector in SAMPLE_CONNECTORS:
        if connector["type"] == connector_type:
            return connector.copy()
    return None
