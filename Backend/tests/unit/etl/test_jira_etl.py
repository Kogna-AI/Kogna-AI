"""
Unit tests for services/etl/jira_etl.py

Tests Jira data cleaning and transformation functions.
"""

import pytest
from datetime import datetime


class TestCleanJiraIssue:
    """Tests for clean_jira_issue function."""

    @pytest.fixture
    def raw_jira_issue(self):
        """Sample raw Jira issue with all the API noise."""
        return {
            "id": "10001",
            "key": "PROJ-123",
            "self": "https://jira.example.com/rest/api/3/issue/10001",
            "fields": {
                "summary": "Implement new feature",
                "description": "As a user, I want to do something",
                "status": {
                    "self": "https://jira.example.com/status/3",
                    "id": "3",
                    "name": "In Progress",
                    "statusCategory": {
                        "self": "https://jira.example.com/statuscategory/4",
                        "id": 4,
                        "key": "indeterminate",
                        "name": "In Progress"
                    }
                },
                "assignee": {
                    "self": "https://jira.example.com/user/123",
                    "accountId": "123456:abcdef",
                    "displayName": "John Doe",
                    "emailAddress": "john@example.com",
                    "avatarUrls": {
                        "48x48": "https://avatar.example.com/48",
                        "24x24": "https://avatar.example.com/24"
                    }
                },
                "reporter": {
                    "self": "https://jira.example.com/user/456",
                    "accountId": "654321:fedcba",
                    "displayName": "Jane Doe",
                    "avatarUrls": {
                        "48x48": "https://avatar.example.com/48"
                    }
                },
                "priority": {
                    "self": "https://jira.example.com/priority/2",
                    "id": "2",
                    "name": "High",
                    "iconUrl": "https://jira.example.com/images/high.svg"
                },
                "issuetype": {
                    "self": "https://jira.example.com/issuetype/10001",
                    "id": "10001",
                    "name": "Story",
                    "iconUrl": "https://jira.example.com/images/story.svg"
                },
                "project": {
                    "self": "https://jira.example.com/project/10000",
                    "id": "10000",
                    "key": "PROJ",
                    "name": "Project Alpha",
                    "avatarUrls": {
                        "48x48": "https://avatar.example.com/project/48"
                    }
                },
                "created": "2024-01-15T10:00:00.000+0000",
                "updated": "2024-01-16T15:30:00.000+0000",
                "labels": ["backend", "api"],
                "components": [
                    {"self": "https://jira.example.com/component/1", "name": "Backend"},
                    {"self": "https://jira.example.com/component/2", "name": "API"}
                ],
                "timetracking": {
                    "originalEstimate": "2d",
                    "timeSpent": "4h",
                    "remainingEstimate": "1d 4h"
                },
                "duedate": "2024-01-20",
                "sprint": {
                    "id": 100,
                    "name": "Sprint 5",
                    "state": "active"
                }
            }
        }

    def test_extracts_basic_fields(self, raw_jira_issue):
        """Should extract basic issue fields."""
        from services.etl.jira_etl import clean_jira_issue

        result = clean_jira_issue(raw_jira_issue)

        assert result["issue_key"] == "PROJ-123"
        assert result["issue_id"] == "10001"
        assert result["summary"] == "Implement new feature"
        assert result["description"] == "As a user, I want to do something"

    def test_extracts_status_info(self, raw_jira_issue):
        """Should extract status name and category."""
        from services.etl.jira_etl import clean_jira_issue

        result = clean_jira_issue(raw_jira_issue)

        assert result["status"] == "In Progress"
        assert result["status_category"] == "In Progress"

    def test_extracts_assignee_name_only(self, raw_jira_issue):
        """Should extract only displayName, not accountId or avatarUrls."""
        from services.etl.jira_etl import clean_jira_issue

        result = clean_jira_issue(raw_jira_issue)

        assert result["assignee"] == "John Doe"
        # Should NOT contain these
        assert "accountId" not in str(result)
        assert "avatarUrls" not in str(result)

    def test_extracts_reporter_name_only(self, raw_jira_issue):
        """Should extract only reporter displayName."""
        from services.etl.jira_etl import clean_jira_issue

        result = clean_jira_issue(raw_jira_issue)

        assert result["reporter"] == "Jane Doe"

    def test_extracts_priority_name(self, raw_jira_issue):
        """Should extract priority name without iconUrl."""
        from services.etl.jira_etl import clean_jira_issue

        result = clean_jira_issue(raw_jira_issue)

        assert result["priority"] == "High"
        assert "iconUrl" not in str(result)

    def test_extracts_issue_type(self, raw_jira_issue):
        """Should extract issue type name."""
        from services.etl.jira_etl import clean_jira_issue

        result = clean_jira_issue(raw_jira_issue)

        assert result["issue_type"] == "Story"

    def test_extracts_project_info(self, raw_jira_issue):
        """Should extract project key and name only."""
        from services.etl.jira_etl import clean_jira_issue

        result = clean_jira_issue(raw_jira_issue)

        assert result["project"]["key"] == "PROJ"
        assert result["project"]["name"] == "Project Alpha"
        # Should NOT contain avatar URLs
        assert "avatarUrls" not in str(result["project"])

    def test_formats_dates_as_human_readable(self, raw_jira_issue):
        """Should format dates as human-readable strings."""
        from services.etl.jira_etl import clean_jira_issue

        result = clean_jira_issue(raw_jira_issue)

        # Should be formatted like '2024-01-15 10:00'
        assert "2024-01-15" in result["created"]
        assert result["created_date"] == "2024-01-15"
        assert result["updated_date"] == "2024-01-16"

    def test_extracts_labels(self, raw_jira_issue):
        """Should extract labels as list."""
        from services.etl.jira_etl import clean_jira_issue

        result = clean_jira_issue(raw_jira_issue)

        assert result["labels"] == ["backend", "api"]

    def test_extracts_component_names(self, raw_jira_issue):
        """Should extract component names only, not self URLs."""
        from services.etl.jira_etl import clean_jira_issue

        result = clean_jira_issue(raw_jira_issue)

        assert result["components"] == ["Backend", "API"]
        assert "self" not in str(result.get("components", []))

    def test_extracts_time_tracking(self, raw_jira_issue):
        """Should extract time tracking estimates."""
        from services.etl.jira_etl import clean_jira_issue

        result = clean_jira_issue(raw_jira_issue)

        assert result["time_tracking"]["estimated"] == "2d"
        assert result["time_tracking"]["spent"] == "4h"
        assert result["time_tracking"]["remaining"] == "1d 4h"

    def test_extracts_due_date(self, raw_jira_issue):
        """Should extract due date."""
        from services.etl.jira_etl import clean_jira_issue

        result = clean_jira_issue(raw_jira_issue)

        assert result["due_date"] == "2024-01-20"

    def test_extracts_sprint_name(self, raw_jira_issue):
        """Should extract sprint name only."""
        from services.etl.jira_etl import clean_jira_issue

        result = clean_jira_issue(raw_jira_issue)

        assert result["sprint"] == "Sprint 5"

    def test_handles_unassigned_issue(self):
        """Should handle issue with no assignee."""
        from services.etl.jira_etl import clean_jira_issue

        raw_issue = {
            "key": "PROJ-456",
            "fields": {
                "summary": "Unassigned task",
                "assignee": None,
                "status": {"name": "Open"}
            }
        }

        result = clean_jira_issue(raw_issue)

        assert result["assignee"] == "Unassigned"

    def test_handles_missing_optional_fields(self):
        """Should handle missing optional fields gracefully."""
        from services.etl.jira_etl import clean_jira_issue

        raw_issue = {
            "key": "PROJ-789",
            "fields": {
                "summary": "Minimal issue"
            }
        }

        result = clean_jira_issue(raw_issue)

        assert result["issue_key"] == "PROJ-789"
        assert result["summary"] == "Minimal issue"
        # Optional fields should be None or not present
        assert "labels" not in result or result.get("labels") is None
        assert "sprint" not in result or result.get("sprint") is None

    def test_handles_malformed_issue(self):
        """Should return minimal structure on error."""
        from services.etl.jira_etl import clean_jira_issue

        # Completely empty issue
        result = clean_jira_issue({})

        assert result["issue_key"] == "Unknown"

    def test_sprint_as_list(self):
        """Should handle sprint as list (some Jira versions return list)."""
        from services.etl.jira_etl import clean_jira_issue

        raw_issue = {
            "key": "PROJ-100",
            "fields": {
                "summary": "Test",
                "sprint": [
                    {"id": 1, "name": "Sprint 1", "state": "active"},
                    {"id": 2, "name": "Sprint 2", "state": "closed"}
                ]
            }
        }

        result = clean_jira_issue(raw_issue)

        assert result["sprint"] == "Sprint 1"  # Takes first sprint


class TestCleanJiraIssues:
    """Tests for clean_jira_issues batch function."""

    def test_cleans_multiple_issues(self):
        """Should clean all issues in list."""
        from services.etl.jira_etl import clean_jira_issues

        raw_issues = [
            {"key": "PROJ-1", "fields": {"summary": "Issue 1"}},
            {"key": "PROJ-2", "fields": {"summary": "Issue 2"}},
            {"key": "PROJ-3", "fields": {"summary": "Issue 3"}},
        ]

        result = clean_jira_issues(raw_issues)

        assert len(result) == 3
        assert result[0]["issue_key"] == "PROJ-1"
        assert result[1]["issue_key"] == "PROJ-2"
        assert result[2]["issue_key"] == "PROJ-3"

    def test_handles_empty_list(self):
        """Should return empty list for empty input."""
        from services.etl.jira_etl import clean_jira_issues

        result = clean_jira_issues([])

        assert result == []


class TestCreateJiraSearchableText:
    """Tests for create_jira_searchable_text function."""

    def test_creates_formatted_text(self):
        """Should create human-readable text for embeddings."""
        from services.etl.jira_etl import create_jira_searchable_text

        cleaned_issue = {
            "issue_key": "PROJ-123",
            "issue_type": "Story",
            "status": "In Progress",
            "summary": "Implement new feature",
            "description": "User story description",
            "project": {"key": "PROJ", "name": "Project Alpha"},
            "assignee": "John Doe",
            "reporter": "Jane Doe",
            "priority": "High",
            "created": "2024-01-15 10:00",
            "updated": "2024-01-16 15:30",
            "labels": ["backend", "api"],
        }

        result = create_jira_searchable_text(cleaned_issue)

        assert "Issue: PROJ-123" in result
        assert "Type: Story" in result
        assert "Status: In Progress" in result
        assert "Summary: Implement new feature" in result
        assert "Description: User story description" in result
        assert "Project: Project Alpha" in result
        assert "Assignee: John Doe" in result
        assert "Reporter: Jane Doe" in result
        assert "Priority: High" in result
        assert "Created: 2024-01-15 10:00" in result
        assert "Labels: backend, api" in result

    def test_handles_minimal_issue(self):
        """Should handle issue with minimal fields."""
        from services.etl.jira_etl import create_jira_searchable_text

        cleaned_issue = {
            "issue_key": "PROJ-1",
            "issue_type": "Task",
            "status": "Open",
        }

        result = create_jira_searchable_text(cleaned_issue)

        assert "Issue: PROJ-1" in result
        assert "Type: Task" in result
        assert "Status: Open" in result

    def test_includes_time_tracking(self):
        """Should include time tracking if present."""
        from services.etl.jira_etl import create_jira_searchable_text

        cleaned_issue = {
            "issue_key": "PROJ-1",
            "issue_type": "Task",
            "status": "Open",
            "time_tracking": {
                "estimated": "2d",
                "spent": "4h",
                "remaining": "1d 4h"
            }
        }

        result = create_jira_searchable_text(cleaned_issue)

        assert "Time Estimated: 2d" in result
        assert "Time Spent: 4h" in result
        assert "Time Remaining: 1d 4h" in result

    def test_includes_sprint(self):
        """Should include sprint if present."""
        from services.etl.jira_etl import create_jira_searchable_text

        cleaned_issue = {
            "issue_key": "PROJ-1",
            "issue_type": "Task",
            "status": "Open",
            "sprint": "Sprint 5"
        }

        result = create_jira_searchable_text(cleaned_issue)

        assert "Sprint: Sprint 5" in result

    def test_includes_components(self):
        """Should include components if present."""
        from services.etl.jira_etl import create_jira_searchable_text

        cleaned_issue = {
            "issue_key": "PROJ-1",
            "issue_type": "Task",
            "status": "Open",
            "components": ["Backend", "API"]
        }

        result = create_jira_searchable_text(cleaned_issue)

        assert "Components: Backend, API" in result


class TestRunJiraETL:
    """Tests for run_jira_etl async function."""

    @pytest.mark.asyncio
    async def test_returns_tuple(self):
        """Should return (success, processed, skipped) tuple."""
        from unittest.mock import patch, AsyncMock, MagicMock

        with patch("services.etl.jira_etl.httpx.AsyncClient") as mock_client:
            # Mock the async context manager
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            # Mock API responses
            mock_instance.get.side_effect = [
                # accessible-resources
                MagicMock(json=lambda: [{"id": "cloud-123"}], raise_for_status=lambda: None),
                # projects
                MagicMock(json=lambda: [], raise_for_status=lambda: None)
            ]

            with patch("services.etl.jira_etl.complete_sync_job", new_callable=AsyncMock):
                with patch("services.etl.jira_etl.update_sync_progress", new_callable=AsyncMock):
                    from services.etl.jira_etl import run_jira_etl

                    result = await run_jira_etl(
                        user_id="user-123",
                        access_token="test-token"
                    )

        assert isinstance(result, tuple)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_handles_no_accessible_resources(self):
        """Should return failure when no Jira resources accessible."""
        from unittest.mock import patch, AsyncMock, MagicMock

        with patch("services.etl.jira_etl.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            # Return empty resources
            mock_instance.get.return_value = MagicMock(
                json=lambda: [],
                raise_for_status=lambda: None
            )

            with patch("services.etl.jira_etl.complete_sync_job", new_callable=AsyncMock):
                from services.etl.jira_etl import run_jira_etl

                success, processed, skipped = await run_jira_etl(
                    user_id="user-123",
                    access_token="test-token"
                )

        assert success is False
        assert processed == 0
        assert skipped == 0
