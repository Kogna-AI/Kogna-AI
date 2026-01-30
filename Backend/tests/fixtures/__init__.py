"""
Test fixtures package.

This package provides:
- Factory Boy factories for generating test data (factories.py)
- Static sample data for common test scenarios (sample_data.py)

Usage:
    from tests.fixtures import UserFactory, create_users
    from tests.fixtures import SAMPLE_USERS, SAMPLE_TEAMS

Note: Factory imports require factory-boy to be installed.
      Sample data imports work without additional dependencies.
"""

# Try to import factories (requires factory-boy package)
try:
    from tests.fixtures.factories import (
        # User factories
        UserFactory,
        AdminUserFactory,
        # Organization factories
        OrganizationFactory,
        TeamFactory,
        TeamMemberFactory,
        # Business object factories
        ObjectiveFactory,
        KPIFactory,
        InsightFactory,
        # ETL data factories
        JiraIssueFactory,
        GoogleDriveFileFactory,
        ConnectorTokenFactory,
        # Chat factories
        ConversationFactory,
        MessageFactory,
        # Batch creation helpers
        create_users,
        create_teams,
        create_kpis,
        create_objectives,
    )
    _FACTORIES_AVAILABLE = True
except ImportError:
    _FACTORIES_AVAILABLE = False
    # Define placeholder for when factory-boy is not installed
    UserFactory = None
    AdminUserFactory = None
    OrganizationFactory = None
    TeamFactory = None
    TeamMemberFactory = None
    ObjectiveFactory = None
    KPIFactory = None
    InsightFactory = None
    JiraIssueFactory = None
    GoogleDriveFileFactory = None
    ConnectorTokenFactory = None
    ConversationFactory = None
    MessageFactory = None
    create_users = None
    create_teams = None
    create_kpis = None
    create_objectives = None

# Sample data imports (no external dependencies)
from tests.fixtures.sample_data import (
    # Sample user data
    SAMPLE_USERS,
    SAMPLE_ADMIN_USER,
    # Sample organization data
    SAMPLE_ORGANIZATION,
    SAMPLE_TEAMS,
    SAMPLE_TEAM_MEMBERS,
    # Sample business objects
    SAMPLE_OBJECTIVES,
    SAMPLE_KPIS,
    SAMPLE_INSIGHTS,
    # Sample ETL data
    SAMPLE_JIRA_ISSUES,
    SAMPLE_GOOGLE_DRIVE_FILES,
    SAMPLE_CONNECTORS,
    # Sample chat data
    SAMPLE_CONVERSATIONS,
    SAMPLE_MESSAGES,
    # API response samples
    SAMPLE_KPI_DASHBOARD_RESPONSE,
    SAMPLE_INSIGHTS_RESPONSE,
    # Error response samples
    SAMPLE_ERROR_RESPONSES,
    # Helper functions
    get_user_by_id,
    get_team_by_id,
    get_kpi_by_id,
    get_objective_by_id,
    get_connector_by_type,
)

__all__ = [
    # Factories (may be None if factory-boy not installed)
    "UserFactory",
    "AdminUserFactory",
    "OrganizationFactory",
    "TeamFactory",
    "TeamMemberFactory",
    "ObjectiveFactory",
    "KPIFactory",
    "InsightFactory",
    "JiraIssueFactory",
    "GoogleDriveFileFactory",
    "ConnectorTokenFactory",
    "ConversationFactory",
    "MessageFactory",
    # Batch helpers (may be None if factory-boy not installed)
    "create_users",
    "create_teams",
    "create_kpis",
    "create_objectives",
    # Sample data
    "SAMPLE_USERS",
    "SAMPLE_ADMIN_USER",
    "SAMPLE_ORGANIZATION",
    "SAMPLE_TEAMS",
    "SAMPLE_TEAM_MEMBERS",
    "SAMPLE_OBJECTIVES",
    "SAMPLE_KPIS",
    "SAMPLE_INSIGHTS",
    "SAMPLE_JIRA_ISSUES",
    "SAMPLE_GOOGLE_DRIVE_FILES",
    "SAMPLE_CONNECTORS",
    "SAMPLE_CONVERSATIONS",
    "SAMPLE_MESSAGES",
    "SAMPLE_KPI_DASHBOARD_RESPONSE",
    "SAMPLE_INSIGHTS_RESPONSE",
    "SAMPLE_ERROR_RESPONSES",
    # Helper functions
    "get_user_by_id",
    "get_team_by_id",
    "get_kpi_by_id",
    "get_objective_by_id",
    "get_connector_by_type",
]
