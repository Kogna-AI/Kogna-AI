"""
KPI Summary Service

Generates natural language summaries from KPI data for embedding into the vector database.
This enables AI agents to discover and understand KPI information through conversational queries.
"""

from typing import Dict, List, Optional
import logging
from supabase_connect import get_supabase_manager

logger = logging.getLogger(__name__)

try:
    supabase = get_supabase_manager().client
except Exception as e:
    logger.error(f"Failed to initialize Supabase in kpi_summary_service: {e}")
    supabase = None


async def generate_kpi_summary_text(
    kpi_data: Dict,
    organization_id: str,
    connector_type: str,
    source_id: str,
    include_trends: bool = True
) -> str:
    """
    Generates natural language summary from KPI data.

    Args:
        kpi_data: KPI record from connector_kpis table with keys:
                  kpi_name, kpi_category, kpi_value, kpi_unit, source_name,
                  extracted_at, period_start, period_end
        organization_id: Organization UUID
        connector_type: Type of connector (jira, google_drive, etc.)
        source_id: Source identifier (project key, board ID, etc.)
        include_trends: Whether to include trend analysis from materialized view

    Returns:
        Natural language summary string ready for embedding

    Example:
        "The velocity metric 'issues_completed_7_days' for Project ABC (jira)
        is 12 issues from 2024-01-01 to 2024-01-08. The trend is up with a
        15.3% increase from the previous day. The 7-day moving average is 10.5."
    """
    # Extract KPI details
    kpi_name = kpi_data.get('kpi_name', 'Unknown KPI')
    kpi_category = kpi_data.get('kpi_category', 'general')
    kpi_value = kpi_data.get('kpi_value', {})
    kpi_unit = kpi_data.get('kpi_unit', '')
    source_name = kpi_data.get('source_name', source_id)
    extracted_at = kpi_data.get('extracted_at')
    period_start = kpi_data.get('period_start')
    period_end = kpi_data.get('period_end')

    # Format value based on JSONB structure
    if isinstance(kpi_value, dict):
        value_str = str(kpi_value.get('value', kpi_value))
    else:
        value_str = str(kpi_value)

    # Build summary parts
    summary_parts = []

    # Time context
    time_context = ""
    if period_start and period_end:
        # Format dates if they're ISO strings
        try:
            start_date = period_start if isinstance(period_start, str) else period_start.isoformat()
            end_date = period_end if isinstance(period_end, str) else period_end.isoformat()
            time_context = f"from {start_date[:10]} to {end_date[:10]}"
        except:
            time_context = f"from {period_start} to {period_end}"
    elif extracted_at:
        try:
            extracted_date = extracted_at if isinstance(extracted_at, str) else extracted_at.isoformat()
            time_context = f"as of {extracted_date[:10]}"
        except:
            time_context = f"as of {extracted_at}"

    # Main KPI statement
    summary_parts.append(
        f"The {kpi_category} metric '{kpi_name}' for {source_name} ({connector_type}) "
        f"is {value_str} {kpi_unit} {time_context}."
    )

    # Add trend data if requested
    if include_trends:
        trend_data = await get_kpi_trend_data(
            organization_id, connector_type, source_id, kpi_name
        )
        if trend_data:
            trend_summary = format_trend_summary(trend_data)
            if trend_summary:
                summary_parts.append(trend_summary)

    # Add contextual interpretation
    interpretation = generate_kpi_interpretation(
        kpi_category, kpi_name, value_str, kpi_unit
    )
    if interpretation:
        summary_parts.append(interpretation)

    return " ".join(summary_parts)


async def get_kpi_trend_data(
    organization_id: str,
    connector_type: str,
    source_id: str,
    kpi_name: str,
    days_back: int = 30
) -> Optional[Dict]:
    """
    Fetches trend data from mv_connector_kpi_trends materialized view.

    Args:
        organization_id: Organization UUID
        connector_type: Connector type (jira, etc.)
        source_id: Source identifier
        kpi_name: Name of the KPI
        days_back: Number of days to look back (default: 30)

    Returns:
        Dictionary with trend_direction, day_over_day_change, moving_avg_7day, etc.
        Returns None if no trend data available or on error.
    """
    if not supabase:
        logger.warning("Supabase client not available for trend query")
        return None

    try:
        # Call the Supabase RPC function
        response = supabase.rpc(
            "get_kpi_trend",
            {
                "p_organization_id": organization_id,
                "p_connector_type": connector_type,
                "p_source_id": source_id,
                "p_kpi_name": kpi_name,
                "p_days_back": days_back
            }
        ).execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        return None

    except Exception as e:
        logger.warning(f"Could not fetch trend data for {kpi_name}: {e}")
        return None


def format_trend_summary(trend_data: Dict) -> str:
    """
    Formats trend data into natural language.

    Args:
        trend_data: Dictionary from get_kpi_trend_data() containing:
                   trend_direction, day_over_day_change, moving_avg_7day, etc.

    Returns:
        Natural language trend summary string
    """
    trend_direction = trend_data.get('trend_direction', 'stable')
    day_over_day_change = trend_data.get('day_over_day_change')
    moving_avg = trend_data.get('moving_avg_7day')

    parts = []

    # Trend direction
    if trend_direction and trend_direction not in ['n/a', 'stable']:
        parts.append(f"The trend is {trend_direction}")
    elif trend_direction == 'stable':
        parts.append("The trend is stable")

    # Day-over-day change
    if day_over_day_change is not None:
        try:
            change_pct = float(day_over_day_change)
            if abs(change_pct) > 0.1:  # Only mention if change is significant
                direction = 'increase' if change_pct > 0 else 'decrease'
                parts.append(f"with a {abs(change_pct):.1f}% {direction} from the previous day")
        except (ValueError, TypeError) as e:
            logger.debug(
                "Unable to parse day_over_day_change as float in format_trend_summary; "
                "skipping day-over-day change detail. Raw value: %r. Error: %s",
                day_over_day_change,
                e,
            )

    # Moving average
    if moving_avg is not None:
        try:
            avg_value = float(moving_avg)
            parts.append(f"The 7-day moving average is {avg_value:.2f}")
        except (ValueError, TypeError) as e:
            logger.debug(
                "Unable to parse moving_avg_7day as float in format_trend_summary; "
                "skipping moving average detail. Raw value: %r. Error: %s",
                moving_avg,
                e,
            )

    if parts:
        return ". ".join(parts) + "."
    return ""


def generate_kpi_interpretation(
    category: str,
    kpi_name: str,
    value: str,
    unit: str
) -> str:
    """
    Generates contextual interpretation based on KPI type.

    Provides human-readable context about what a KPI measures and why it matters.

    Args:
        category: KPI category (velocity, burndown, productivity, quality, etc.)
        kpi_name: Specific KPI name
        value: Current value as string
        unit: Unit of measurement

    Returns:
        Contextual interpretation string
    """
    # Define interpretations for known KPI types
    interpretations = {
        ('velocity', 'issues_completed_7_days'):
            "This indicates the team's velocity in completing work items over the past week.",
        ('velocity', 'average_cycle_time_days'):
            "This represents the average time from start to completion for work items.",
        ('burndown', 'completion_percentage'):
            "This shows what percentage of planned work has been completed.",
        ('productivity', 'active_assignees'):
            "This represents the number of team members actively working on tasks.",
        ('productivity', 'unassigned_count'):
            "This indicates the number of work items that have not been assigned to anyone.",
        ('quality', 'high_priority_count'):
            "This indicates the number of high-priority items requiring immediate attention.",
    }

    # Try exact match first
    interpretation = interpretations.get((category, kpi_name))
    if interpretation:
        return interpretation

    # Fallback to category-level interpretation
    category_interpretations = {
        'velocity': "This metric tracks team velocity and throughput.",
        'burndown': "This metric tracks progress toward completion goals.",
        'productivity': "This metric measures team productivity and resource allocation.",
        'quality': "This metric assesses work quality and priority management.",
        'collaboration': "This metric measures team collaboration and communication.",
        'financial': "This metric tracks cost and budget performance.",
    }

    return category_interpretations.get(category, "")


# Example usage
if __name__ == "__main__":
    # Example KPI data
    example_kpi = {
        'kpi_name': 'issues_completed_7_days',
        'kpi_category': 'velocity',
        'kpi_value': {'value': 12, 'type': 'numeric'},
        'kpi_unit': 'issues',
        'source_name': 'Project ABC',
        'extracted_at': '2024-01-09T10:00:00Z',
        'period_start': '2024-01-02T00:00:00Z',
        'period_end': '2024-01-09T00:00:00Z'
    }

    # This would generate something like:
    # "The velocity metric 'issues_completed_7_days' for Project ABC (jira) is 12 issues
    # from 2024-01-02 to 2024-01-09. This indicates the team's velocity in completing work
    # items over the past week."

    print("KPI Summary Service loaded successfully")
