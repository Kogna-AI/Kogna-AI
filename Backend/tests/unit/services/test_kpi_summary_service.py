"""
Unit tests for services/kpi_summary_service.py

Tests KPI summary generation and trend formatting functions.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestGenerateKpiInterpretation:
    """Tests for generate_kpi_interpretation function."""

    def test_velocity_issues_completed(self):
        """Should return interpretation for velocity issues_completed_7_days."""
        from services.kpi_summary_service import generate_kpi_interpretation

        result = generate_kpi_interpretation(
            category="velocity",
            kpi_name="issues_completed_7_days",
            value="12",
            unit="issues"
        )

        assert "velocity" in result.lower()
        assert "completing" in result.lower() or "completed" in result.lower()

    def test_velocity_cycle_time(self):
        """Should return interpretation for average_cycle_time_days."""
        from services.kpi_summary_service import generate_kpi_interpretation

        result = generate_kpi_interpretation(
            category="velocity",
            kpi_name="average_cycle_time_days",
            value="3.5",
            unit="days"
        )

        assert "time" in result.lower()

    def test_burndown_completion(self):
        """Should return interpretation for completion_percentage."""
        from services.kpi_summary_service import generate_kpi_interpretation

        result = generate_kpi_interpretation(
            category="burndown",
            kpi_name="completion_percentage",
            value="75",
            unit="%"
        )

        assert "completed" in result.lower() or "completion" in result.lower()

    def test_productivity_active_assignees(self):
        """Should return interpretation for active_assignees."""
        from services.kpi_summary_service import generate_kpi_interpretation

        result = generate_kpi_interpretation(
            category="productivity",
            kpi_name="active_assignees",
            value="5",
            unit="members"
        )

        assert "team members" in result.lower() or "working" in result.lower()

    def test_quality_high_priority(self):
        """Should return interpretation for high_priority_count."""
        from services.kpi_summary_service import generate_kpi_interpretation

        result = generate_kpi_interpretation(
            category="quality",
            kpi_name="high_priority_count",
            value="3",
            unit="items"
        )

        assert "priority" in result.lower()

    def test_fallback_to_category_interpretation(self):
        """Should fall back to category-level interpretation for unknown KPI."""
        from services.kpi_summary_service import generate_kpi_interpretation

        result = generate_kpi_interpretation(
            category="velocity",
            kpi_name="unknown_metric",
            value="100",
            unit="items"
        )

        assert "velocity" in result.lower()

    def test_unknown_category_returns_empty(self):
        """Should return empty string for unknown category."""
        from services.kpi_summary_service import generate_kpi_interpretation

        result = generate_kpi_interpretation(
            category="unknown_category",
            kpi_name="unknown_metric",
            value="100",
            unit="items"
        )

        assert result == ""


class TestFormatTrendSummary:
    """Tests for format_trend_summary function."""

    def test_up_trend_with_change(self):
        """Should format upward trend with percentage change."""
        from services.kpi_summary_service import format_trend_summary

        trend_data = {
            "trend_direction": "up",
            "day_over_day_change": 15.3,
            "moving_avg_7day": 10.5
        }

        result = format_trend_summary(trend_data)

        assert "up" in result.lower()
        assert "15.3%" in result
        assert "increase" in result.lower()
        assert "10.5" in result

    def test_down_trend_with_change(self):
        """Should format downward trend with decrease."""
        from services.kpi_summary_service import format_trend_summary

        trend_data = {
            "trend_direction": "down",
            "day_over_day_change": -8.5,
            "moving_avg_7day": 12.0
        }

        result = format_trend_summary(trend_data)

        assert "down" in result.lower()
        assert "8.5%" in result
        assert "decrease" in result.lower()

    def test_stable_trend(self):
        """Should format stable trend."""
        from services.kpi_summary_service import format_trend_summary

        trend_data = {
            "trend_direction": "stable",
            "day_over_day_change": 0.05,  # Below threshold
            "moving_avg_7day": 10.0
        }

        result = format_trend_summary(trend_data)

        assert "stable" in result.lower()

    def test_no_significant_change(self):
        """Should skip change detail if below threshold."""
        from services.kpi_summary_service import format_trend_summary

        trend_data = {
            "trend_direction": "stable",
            "day_over_day_change": 0.05,  # Below 0.1 threshold
            "moving_avg_7day": 10.0
        }

        result = format_trend_summary(trend_data)

        # Should not mention the tiny change percentage
        assert "0.05%" not in result

    def test_handles_missing_fields(self):
        """Should handle missing optional fields gracefully."""
        from services.kpi_summary_service import format_trend_summary

        trend_data = {
            "trend_direction": "up"
        }

        result = format_trend_summary(trend_data)

        assert "up" in result.lower()

    def test_handles_none_values(self):
        """Should handle None values in trend data."""
        from services.kpi_summary_service import format_trend_summary

        trend_data = {
            "trend_direction": "stable",
            "day_over_day_change": None,
            "moving_avg_7day": None
        }

        result = format_trend_summary(trend_data)

        # Should not crash, should return some result
        assert isinstance(result, str)

    def test_handles_invalid_numeric_values(self):
        """Should handle non-numeric values gracefully."""
        from services.kpi_summary_service import format_trend_summary

        trend_data = {
            "trend_direction": "up",
            "day_over_day_change": "invalid",
            "moving_avg_7day": "not a number"
        }

        result = format_trend_summary(trend_data)

        # Should not crash
        assert isinstance(result, str)

    def test_na_trend_direction(self):
        """Should handle n/a trend direction."""
        from services.kpi_summary_service import format_trend_summary

        trend_data = {
            "trend_direction": "n/a",
            "moving_avg_7day": 10.0
        }

        result = format_trend_summary(trend_data)

        # Should not include "n/a" as trend description
        assert "n/a" not in result.lower() or result == ""


class TestGetKpiTrendData:
    """Tests for get_kpi_trend_data async function."""

    @pytest.mark.asyncio
    async def test_returns_trend_data(self):
        """Should return trend data from RPC call."""
        with patch("services.kpi_summary_service.supabase") as mock_supabase:
            mock_rpc = MagicMock()
            mock_supabase.rpc.return_value = mock_rpc
            mock_rpc.execute.return_value = MagicMock(
                data=[{
                    "trend_direction": "up",
                    "day_over_day_change": 5.0,
                    "moving_avg_7day": 10.0
                }]
            )

            from services.kpi_summary_service import get_kpi_trend_data

            result = await get_kpi_trend_data(
                organization_id="org-123",
                connector_type="jira",
                source_id="PROJ",
                kpi_name="issues_completed_7_days"
            )

        assert result["trend_direction"] == "up"
        assert result["day_over_day_change"] == 5.0

    @pytest.mark.asyncio
    async def test_returns_none_when_no_data(self):
        """Should return None when no trend data available."""
        with patch("services.kpi_summary_service.supabase") as mock_supabase:
            mock_rpc = MagicMock()
            mock_supabase.rpc.return_value = mock_rpc
            mock_rpc.execute.return_value = MagicMock(data=[])

            from services.kpi_summary_service import get_kpi_trend_data

            result = await get_kpi_trend_data(
                organization_id="org-123",
                connector_type="jira",
                source_id="PROJ",
                kpi_name="unknown_kpi"
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_handles_rpc_error(self):
        """Should return None on RPC error."""
        with patch("services.kpi_summary_service.supabase") as mock_supabase:
            mock_supabase.rpc.side_effect = Exception("RPC failed")

            from services.kpi_summary_service import get_kpi_trend_data

            result = await get_kpi_trend_data(
                organization_id="org-123",
                connector_type="jira",
                source_id="PROJ",
                kpi_name="issues_completed_7_days"
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_supabase_not_available(self):
        """Should return None when supabase client is not available."""
        with patch("services.kpi_summary_service.supabase", None):
            from services.kpi_summary_service import get_kpi_trend_data

            result = await get_kpi_trend_data(
                organization_id="org-123",
                connector_type="jira",
                source_id="PROJ",
                kpi_name="issues_completed_7_days"
            )

        assert result is None


class TestGenerateKpiSummaryText:
    """Tests for generate_kpi_summary_text async function."""

    @pytest.mark.asyncio
    async def test_generates_summary_without_trends(self):
        """Should generate summary text without trend data."""
        from services.kpi_summary_service import generate_kpi_summary_text

        kpi_data = {
            "kpi_name": "issues_completed_7_days",
            "kpi_category": "velocity",
            "kpi_value": {"value": 12},
            "kpi_unit": "issues",
            "source_name": "Project ABC",
            "period_start": "2024-01-02T00:00:00Z",
            "period_end": "2024-01-09T00:00:00Z"
        }

        result = await generate_kpi_summary_text(
            kpi_data=kpi_data,
            organization_id="org-123",
            connector_type="jira",
            source_id="PROJ-ABC",
            include_trends=False
        )

        assert "velocity" in result.lower()
        assert "issues_completed_7_days" in result
        assert "Project ABC" in result
        assert "jira" in result
        assert "12" in result
        assert "2024-01-02" in result
        assert "2024-01-09" in result

    @pytest.mark.asyncio
    async def test_includes_trend_data(self):
        """Should include trend data when requested."""
        with patch("services.kpi_summary_service.get_kpi_trend_data", new_callable=AsyncMock) as mock_trend:
            mock_trend.return_value = {
                "trend_direction": "up",
                "day_over_day_change": 15.0,
                "moving_avg_7day": 10.0
            }

            from services.kpi_summary_service import generate_kpi_summary_text

            kpi_data = {
                "kpi_name": "issues_completed_7_days",
                "kpi_category": "velocity",
                "kpi_value": {"value": 12},
                "kpi_unit": "issues",
                "source_name": "Project ABC"
            }

            result = await generate_kpi_summary_text(
                kpi_data=kpi_data,
                organization_id="org-123",
                connector_type="jira",
                source_id="PROJ-ABC",
                include_trends=True
            )

        assert "up" in result.lower()
        assert "15" in result

    @pytest.mark.asyncio
    async def test_handles_dict_kpi_value(self):
        """Should handle JSONB kpi_value format."""
        from services.kpi_summary_service import generate_kpi_summary_text

        kpi_data = {
            "kpi_name": "completion_rate",
            "kpi_category": "burndown",
            "kpi_value": {"value": 75.5, "type": "numeric"},
            "kpi_unit": "%",
            "source_name": "Sprint 5"
        }

        result = await generate_kpi_summary_text(
            kpi_data=kpi_data,
            organization_id="org-123",
            connector_type="jira",
            source_id="sprint-5",
            include_trends=False
        )

        assert "75.5" in result

    @pytest.mark.asyncio
    async def test_handles_simple_kpi_value(self):
        """Should handle simple non-dict kpi_value."""
        from services.kpi_summary_service import generate_kpi_summary_text

        kpi_data = {
            "kpi_name": "active_users",
            "kpi_category": "productivity",
            "kpi_value": 42,  # Simple integer
            "kpi_unit": "users",
            "source_name": "Team A"
        }

        result = await generate_kpi_summary_text(
            kpi_data=kpi_data,
            organization_id="org-123",
            connector_type="internal",
            source_id="team-a",
            include_trends=False
        )

        assert "42" in result

    @pytest.mark.asyncio
    async def test_includes_interpretation(self):
        """Should include contextual interpretation."""
        from services.kpi_summary_service import generate_kpi_summary_text

        kpi_data = {
            "kpi_name": "issues_completed_7_days",
            "kpi_category": "velocity",
            "kpi_value": {"value": 12},
            "kpi_unit": "issues",
            "source_name": "Project ABC"
        }

        result = await generate_kpi_summary_text(
            kpi_data=kpi_data,
            organization_id="org-123",
            connector_type="jira",
            source_id="PROJ-ABC",
            include_trends=False
        )

        # Should include interpretation about velocity
        assert "velocity" in result.lower()

    @pytest.mark.asyncio
    async def test_handles_extracted_at_only(self):
        """Should use extracted_at when period dates not available."""
        from services.kpi_summary_service import generate_kpi_summary_text

        kpi_data = {
            "kpi_name": "snapshot_metric",
            "kpi_category": "general",
            "kpi_value": {"value": 100},
            "kpi_unit": "items",
            "source_name": "Snapshot",
            "extracted_at": "2024-01-15T10:00:00Z"
        }

        result = await generate_kpi_summary_text(
            kpi_data=kpi_data,
            organization_id="org-123",
            connector_type="snapshot",
            source_id="snap-1",
            include_trends=False
        )

        assert "2024-01-15" in result
        assert "as of" in result.lower()

    @pytest.mark.asyncio
    async def test_handles_missing_source_name(self):
        """Should use source_id when source_name not available."""
        from services.kpi_summary_service import generate_kpi_summary_text

        kpi_data = {
            "kpi_name": "metric",
            "kpi_category": "general",
            "kpi_value": {"value": 50},
            "kpi_unit": "items"
            # No source_name
        }

        result = await generate_kpi_summary_text(
            kpi_data=kpi_data,
            organization_id="org-123",
            connector_type="test",
            source_id="source-123",
            include_trends=False
        )

        assert "source-123" in result
