"""
Unit tests for core/permissions.py

Tests UserContext class and permission checking utilities.
"""

import pytest
from unittest.mock import patch, MagicMock

from core.permissions import UserContext


class TestUserContext:
    """Tests for UserContext class."""

    @pytest.fixture
    def basic_user_context(self):
        """Create a basic user context for testing."""
        return UserContext(
            id="user-123",
            supabase_id="supabase-123",
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

    def test_initialization(self, basic_user_context):
        """UserContext should initialize with correct values."""
        ctx = basic_user_context

        assert ctx.id == "user-123"
        assert ctx.supabase_id == "supabase-123"
        assert ctx.email == "test@example.com"
        assert ctx.organization_id == "org-123"
        assert ctx.first_name == "Test"
        assert ctx.second_name == "User"
        assert ctx.role_name == "analyst"
        assert ctx.role_level == 2
        assert len(ctx.permissions) == 3
        assert len(ctx.team_ids) == 2

    def test_has_permission_exact_match(self, basic_user_context):
        """has_permission should return True for exact permission match."""
        ctx = basic_user_context

        assert ctx.has_permission("insights", "read", "team") is True
        assert ctx.has_permission("objectives", "write", "own") is True

    def test_has_permission_no_match(self, basic_user_context):
        """has_permission should return False when permission not present."""
        ctx = basic_user_context

        assert ctx.has_permission("agents", "invoke", "team") is False
        assert ctx.has_permission("kpis", "write", "organization") is False

    def test_has_permission_without_scope(self, basic_user_context):
        """has_permission without scope should check for any scope."""
        ctx = basic_user_context

        # User has insights:read:team, so any "insights:read" should match
        assert ctx.has_permission("insights", "read") is True
        # User doesn't have any "agents:invoke" permission
        assert ctx.has_permission("agents", "invoke") is False

    def test_is_executive_true(self):
        """is_executive should return True for level 4+."""
        ctx = UserContext(
            id="exec-123",
            supabase_id="supabase-123",
            email="exec@example.com",
            organization_id="org-123",
            first_name="Exec",
            second_name="User",
            role_name="executive",
            role_level=4,
            permissions=[],
            team_ids=[],
        )

        assert ctx.is_executive() is True

    def test_is_executive_false(self, basic_user_context):
        """is_executive should return False for level < 4."""
        assert basic_user_context.is_executive() is False

    def test_is_manager_true(self):
        """is_manager should return True for level 3+."""
        ctx = UserContext(
            id="mgr-123",
            supabase_id="supabase-123",
            email="mgr@example.com",
            organization_id="org-123",
            first_name="Manager",
            second_name="User",
            role_name="manager",
            role_level=3,
            permissions=[],
            team_ids=[],
        )

        assert ctx.is_manager() is True

    def test_is_manager_false(self, basic_user_context):
        """is_manager should return False for level < 3."""
        assert basic_user_context.is_manager() is False

    def test_is_analyst_true(self, basic_user_context):
        """is_analyst should return True for level 2+."""
        assert basic_user_context.is_analyst() is True

    def test_is_analyst_false(self):
        """is_analyst should return False for level < 2."""
        ctx = UserContext(
            id="viewer-123",
            supabase_id="supabase-123",
            email="viewer@example.com",
            organization_id="org-123",
            first_name="Viewer",
            second_name="User",
            role_name="viewer",
            role_level=1,
            permissions=[],
            team_ids=[],
        )

        assert ctx.is_analyst() is False

    def test_can_access_organization_data_manager(self):
        """Managers should be able to access organization data."""
        ctx = UserContext(
            id="mgr-123",
            supabase_id="supabase-123",
            email="mgr@example.com",
            organization_id="org-123",
            first_name="Manager",
            second_name="User",
            role_name="manager",
            role_level=3,
            permissions=[],
            team_ids=[],
        )

        assert ctx.can_access_organization_data() is True

    def test_can_access_organization_data_analyst(self, basic_user_context):
        """Analysts should not be able to access organization data."""
        assert basic_user_context.can_access_organization_data() is False

    def test_to_dict(self, basic_user_context):
        """to_dict should return correct dictionary representation."""
        result = basic_user_context.to_dict()

        assert isinstance(result, dict)
        assert result["id"] == "user-123"
        assert result["email"] == "test@example.com"
        assert result["organization_id"] == "org-123"
        assert result["role_name"] == "analyst"
        assert result["role_level"] == 2
        assert result["permissions"] == [
            "insights:read:team",
            "objectives:read:team",
            "objectives:write:own",
        ]
        assert result["team_ids"] == ["team-1", "team-2"]


class TestUserContextRoleLevels:
    """Tests for role level hierarchy."""

    @pytest.mark.parametrize("level,expected_executive,expected_manager,expected_analyst", [
        (1, False, False, False),  # Viewer
        (2, False, False, True),   # Analyst
        (3, False, True, True),    # Manager
        (4, True, True, True),     # Executive
        (5, True, True, True),     # Admin
    ])
    def test_role_level_checks(self, level, expected_executive, expected_manager, expected_analyst):
        """Role level checks should follow hierarchy."""
        ctx = UserContext(
            id="user-123",
            supabase_id="supabase-123",
            email="test@example.com",
            organization_id="org-123",
            first_name="Test",
            second_name="User",
            role_name="test",
            role_level=level,
            permissions=[],
            team_ids=[],
        )

        assert ctx.is_executive() == expected_executive
        assert ctx.is_manager() == expected_manager
        assert ctx.is_analyst() == expected_analyst


class TestUserContextPermissionPatterns:
    """Tests for permission pattern matching."""

    def test_multiple_permissions_same_resource(self):
        """User can have multiple permissions for same resource."""
        ctx = UserContext(
            id="user-123",
            supabase_id="supabase-123",
            email="test@example.com",
            organization_id="org-123",
            first_name="Test",
            second_name="User",
            role_name="manager",
            role_level=3,
            permissions=[
                "objectives:read:team",
                "objectives:read:organization",
                "objectives:write:team",
            ],
            team_ids=["team-1"],
        )

        assert ctx.has_permission("objectives", "read", "team") is True
        assert ctx.has_permission("objectives", "read", "organization") is True
        assert ctx.has_permission("objectives", "write", "team") is True
        assert ctx.has_permission("objectives", "write", "organization") is False

    def test_empty_permissions(self):
        """User with no permissions should fail all checks."""
        ctx = UserContext(
            id="user-123",
            supabase_id="supabase-123",
            email="test@example.com",
            organization_id="org-123",
            first_name="Test",
            second_name="User",
            role_name="viewer",
            role_level=1,
            permissions=[],
            team_ids=[],
        )

        assert ctx.has_permission("insights", "read", "team") is False
        assert ctx.has_permission("insights", "read") is False

    def test_empty_team_ids(self):
        """User with no teams should have empty team_ids list."""
        ctx = UserContext(
            id="user-123",
            supabase_id="supabase-123",
            email="test@example.com",
            organization_id="org-123",
            first_name="Test",
            second_name="User",
            role_name="viewer",
            role_level=1,
            permissions=[],
            team_ids=[],
        )

        assert ctx.team_ids == []
        assert len(ctx.team_ids) == 0


class TestFilterObjectivesByRole:
    """Tests for filter_objectives_by_role helper function."""

    def test_manager_sees_all_objectives(self, mock_manager_context):
        """Managers should see all objectives regardless of team."""
        from core.permissions import filter_objectives_by_role

        objectives = [
            {"id": "obj-1", "team_responsible": "team-1"},
            {"id": "obj-2", "team_responsible": "team-99"},  # Not in manager's teams
            {"id": "obj-3", "team_responsible": "team-2"},
        ]

        result = filter_objectives_by_role(objectives, mock_manager_context)

        assert len(result) == 3
        assert all(obj in result for obj in objectives)

    def test_executive_sees_all_objectives(self, mock_executive_context):
        """Executives should see all objectives."""
        from core.permissions import filter_objectives_by_role

        objectives = [
            {"id": "obj-1", "team_responsible": "team-999"},
            {"id": "obj-2", "team_responsible": "team-888"},
        ]

        result = filter_objectives_by_role(objectives, mock_executive_context)

        assert len(result) == 2

    def test_analyst_sees_only_team_objectives(self, mock_user_context):
        """Analysts should only see objectives for their teams."""
        from core.permissions import filter_objectives_by_role

        objectives = [
            {"id": "obj-1", "team_responsible": "team-1"},  # In user's teams
            {"id": "obj-2", "team_responsible": "team-99"},  # Not in user's teams
            {"id": "obj-3", "team_responsible": "team-2"},  # In user's teams
        ]

        result = filter_objectives_by_role(objectives, mock_user_context)

        assert len(result) == 2
        assert objectives[0] in result
        assert objectives[2] in result
        assert objectives[1] not in result

    def test_empty_objectives_list(self, mock_user_context):
        """Empty objectives list should return empty list."""
        from core.permissions import filter_objectives_by_role

        result = filter_objectives_by_role([], mock_user_context)

        assert result == []


class TestFilterMetricsByRole:
    """Tests for filter_metrics_by_role helper function."""

    def test_manager_sees_all_metrics(self, mock_manager_context):
        """Managers should see all metrics."""
        from core.permissions import filter_metrics_by_role

        metrics = [
            {"id": "metric-1", "value": 100},
            {"id": "metric-2", "value": 200},
        ]

        result = filter_metrics_by_role(metrics, mock_manager_context)

        assert len(result) == 2

    def test_analyst_sees_all_metrics(self, mock_user_context):
        """Analysts should see all metrics (no team filtering for metrics)."""
        from core.permissions import filter_metrics_by_role

        metrics = [
            {"id": "metric-1", "value": 100},
            {"id": "metric-2", "value": 200},
        ]

        result = filter_metrics_by_role(metrics, mock_user_context)

        assert len(result) == 2


class TestGetUserDataScope:
    """Tests for get_user_data_scope helper function."""

    def test_executive_gets_organization_scope(self, mock_executive_context):
        """Executives should have organization scope."""
        from core.permissions import get_user_data_scope

        result = get_user_data_scope(mock_executive_context)

        assert result["scope"] == "organization"
        assert result["organization_id"] == "org-123"
        assert result["user_id"] == "exec-123"
        assert result["role_level"] == 4

    def test_manager_gets_organization_scope(self, mock_manager_context):
        """Managers should have organization scope."""
        from core.permissions import get_user_data_scope

        result = get_user_data_scope(mock_manager_context)

        assert result["scope"] == "organization"
        assert result["organization_id"] == "org-123"

    def test_analyst_with_teams_gets_team_scope(self, mock_user_context):
        """Analysts with teams should have team scope."""
        from core.permissions import get_user_data_scope

        result = get_user_data_scope(mock_user_context)

        assert result["scope"] == "team"
        assert result["team_ids"] == ["team-1", "team-2"]

    def test_user_without_teams_gets_own_scope(self):
        """Users without teams should have own scope."""
        from core.permissions import get_user_data_scope

        ctx = UserContext(
            id="user-123",
            supabase_id="supabase-123",
            email="test@example.com",
            organization_id="org-123",
            first_name="Test",
            second_name="User",
            role_name="viewer",
            role_level=1,
            permissions=[],
            team_ids=[],  # No teams
        )

        result = get_user_data_scope(ctx)

        assert result["scope"] == "own"
        assert result["user_id"] == "user-123"
