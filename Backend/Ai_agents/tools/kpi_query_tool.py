"""
KPI Query Tool

A CrewAI tool for querying real-time KPI metrics from the database.
Provides structured KPI data with trend analysis for AI agents.
"""

from crewai.tools import BaseTool
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class KPIQueryTool(BaseTool):
    """
    Tool for querying real-time KPI data from the database.
    Provides structured KPI data with trend analysis from materialized views.
    """

    name: str = "KPI Database Query Tool"
    description: str = (
        "Use this tool to get REAL-TIME KPI metrics and performance data from the database. "
        "This tool queries the live database for current KPI values, trends, and analytics.\n\n"
        "Use this when the user asks about:\n"
        "- Current team performance metrics (velocity, completion rates, cycle times)\n"
        "- Project or source-specific KPI numbers\n"
        "- Specific KPI values and statistics\n"
        "- Trend analysis or historical comparisons\n"
        "- Team productivity metrics\n"
        "- Work quality indicators (priority counts, etc.)\n\n"
        "Input should be a natural language query like:\n"
        "- 'What is our team velocity for the last 7 days?'\n"
        "- 'Show me completion rates for Jira projects'\n"
        "- 'How many high priority issues do we have?'\n"
        "- 'What are our performance metrics?'\n"
        "- 'Show me velocity trends'"
    )

    supabase_client: Any = None
    user_id: str = ""
    organization_id: str = ""

    def __init__(self, supabase_client: Any, user_id: str, organization_id: str):
        super().__init__()
        self.supabase_client = supabase_client
        self.user_id = user_id
        self.organization_id = organization_id

    def _run(self, query: str) -> str:
        """
        Executes KPI query and returns formatted results.

        Args:
            query: Natural language query string

        Returns:
            Formatted KPI data with trend analysis
        """
        logger.info(f"[KPI Query Tool] Processing query: {query}")

        try:
            # Parse query to extract intent
            query_params = self._parse_query_intent(query)

            # Execute database query based on intent
            kpi_data = self._execute_kpi_query(query_params)

            # Format results with natural language
            formatted_response = self._format_kpi_response(kpi_data, query_params)

            return formatted_response

        except Exception as e:
            logger.error(f"Error in KPIQueryTool: {e}")
            import traceback
            traceback.print_exc()
            return f"Error retrieving KPI data: {str(e)}. The KPI database may be temporarily unavailable."

    def _parse_query_intent(self, query: str) -> Dict[str, Any]:
        """
        Parses natural language query to extract structured parameters.

        Args:
            query: Natural language query string

        Returns:
            Dictionary with extracted parameters:
            - connector_type: Type of connector (jira, google_drive, etc.)
            - kpi_category: Category (velocity, burndown, productivity, quality)
            - source_id: Optional specific source identifier
            - time_period: Number of days to look back (default: 7)
            - kpi_names: List of specific KPI names
        """
        query_lower = query.lower()
        params = {
            'connector_type': None,
            'kpi_category': None,
            'source_id': None,
            'time_period': 7,  # Default to last 7 days
            'kpi_names': []
        }

        # Detect connector type
        if 'jira' in query_lower:
            params['connector_type'] = 'jira'
        elif 'google drive' in query_lower or 'drive' in query_lower:
            params['connector_type'] = 'google_drive'
        elif 'excel' in query_lower or 'microsoft excel' in query_lower:
            params['connector_type'] = 'microsoft_excel'
        elif 'asana' in query_lower:
            params['connector_type'] = 'asana'

        # Detect KPI category
        # Check for more specific burndown-related phrases (like "completion rate") before
        # more general velocity-related terms (like "completion") to avoid misclassification.
        if any(word in query_lower for word in ['burndown', 'progress', 'completion rate']):
            params['kpi_category'] = 'burndown'
        elif any(word in query_lower for word in ['velocity', 'speed', 'throughput', 'completed', 'completion']):
            params['kpi_category'] = 'velocity'
        elif any(word in query_lower for word in ['productivity', 'efficiency', 'assignee', 'workload']):
            params['kpi_category'] = 'productivity'
        elif any(word in query_lower for word in ['quality', 'priority']):
            params['kpi_category'] = 'quality'

        # Detect time period
        if '30 day' in query_lower or 'month' in query_lower or 'last month' in query_lower:
            params['time_period'] = 30
        elif '7 day' in query_lower or 'week' in query_lower or 'last week' in query_lower:
            params['time_period'] = 7
        elif '14 day' in query_lower or 'two week' in query_lower or '2 week' in query_lower:
            params['time_period'] = 14
        elif '90 day' in query_lower or 'quarter' in query_lower:
            params['time_period'] = 90

        # Detect specific KPI mentions
        if 'cycle time' in query_lower:
            params['kpi_names'].append('average_cycle_time_days')
        if 'issues completed' in query_lower or 'completion' in query_lower:
            params['kpi_names'].append('issues_completed_7_days')
        if 'high priority' in query_lower:
            params['kpi_names'].append('high_priority_count')
        if 'assignee' in query_lower:
            params['kpi_names'].extend(['active_assignees', 'unassigned_count'])

        logger.info(f"Parsed query params: {params}")
        return params

    def _execute_kpi_query(self, params: Dict[str, Any]) -> List[Dict]:
        """
        Executes database query to fetch KPI data.

        Args:
            params: Parsed query parameters

        Returns:
            List of KPI trend records from mv_connector_kpi_trends
        """
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=params['time_period'])

            # Build query on materialized view
            query = self.supabase_client.table("mv_connector_kpi_trends").select("*")

            # Apply filters
            query = query.eq("organization_id", self.organization_id)
            query = query.gte("date", start_date.date().isoformat())

            if params['connector_type']:
                query = query.eq("connector_type", params['connector_type'])

            if params['kpi_category']:
                query = query.eq("kpi_category", params['kpi_category'])

            if params['source_id']:
                query = query.eq("source_id", params['source_id'])

            if params['kpi_names']:
                query = query.in_("kpi_name", params['kpi_names'])

            # Execute query
            response = query.order("date", desc=True).limit(100).execute()

            logger.info(f"KPI query returned {len(response.data) if response.data else 0} records")
            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Database query failed: {e}")
            raise

    def _format_kpi_response(self, kpi_data: List[Dict], params: Dict) -> str:
        """
        Formats KPI data into natural language response.

        Args:
            kpi_data: List of KPI records from database
            params: Original query parameters

        Returns:
            Natural language formatted response string
        """
        if not kpi_data:
            return (
                f"No KPI data found for the specified criteria. "
                f"Connector: {params.get('connector_type', 'any')}, "
                f"Category: {params.get('kpi_category', 'any')}, "
                f"Time period: last {params.get('time_period', 7)} days."
            )

        # Group by KPI name and source
        kpis_by_key = {}
        for item in kpi_data:
            kpi_name = item.get('kpi_name', 'Unknown')
            source_id = item.get('source_id', 'Unknown')
            key = f"{source_id}:{kpi_name}"

            if key not in kpis_by_key:
                kpis_by_key[key] = []
            kpis_by_key[key].append(item)

        # Format response
        response_parts = [
            f"Here are the KPI metrics for the last {params.get('time_period', 7)} days:\n"
        ]

        for key, records in kpis_by_key.items():
            latest = records[0]  # Already sorted by date DESC

            # Extract data
            kpi_name = latest.get('kpi_name', 'Unknown')
            kpi_category = latest.get('kpi_category', 'unknown')
            connector_type = latest.get('connector_type', 'unknown')
            kpi_value = latest.get('latest_kpi_value', {})
            kpi_unit = latest.get('kpi_unit', '')
            source_name = latest.get('source_name') or latest.get('source_id', 'Unknown')
            trend_direction = latest.get('trend_direction', 'stable')
            day_change = latest.get('day_over_day_change')
            moving_avg = latest.get('moving_avg_7day')
            date = latest.get('date')

            # Format value
            if isinstance(kpi_value, dict):
                value_str = str(kpi_value.get('value', kpi_value))
            else:
                value_str = str(kpi_value)

            # Build formatted section
            response_parts.append(f"\n**{kpi_name}** - {source_name} ({connector_type})")
            response_parts.append(f"  Category: {kpi_category}")
            response_parts.append(f"  Current Value: {value_str} {kpi_unit} (as of {date})")

            # Add trend information
            if trend_direction and trend_direction != 'n/a':
                response_parts.append(f"  Trend: {trend_direction}")

            if day_change is not None:
                try:
                    change_pct = float(day_change)
                    if abs(change_pct) > 0.1:  # Only show significant changes
                        direction = "increased" if change_pct > 0 else "decreased"
                        response_parts.append(f"  Day-over-day: {direction} by {abs(change_pct):.1f}%")
                except (ValueError, TypeError):
                    pass

            if moving_avg is not None:
                try:
                    avg_value = float(moving_avg)
                    response_parts.append(f"  7-day average: {avg_value:.2f} {kpi_unit}")
                except (ValueError, TypeError):
                    pass

            # Add historical context if multiple records
            if len(records) > 1:
                oldest = records[-1]
                oldest_date = oldest.get('date')
                response_parts.append(f"  Historical data: {len(records)} data points from {oldest_date} to {date}")

        # Add summary
        response_parts.append(f"\n**Summary:**")
        response_parts.append(f"Total KPIs retrieved: {len(kpis_by_key)}")
        response_parts.append(f"Total data points: {len(kpi_data)}")

        # Add categories represented
        categories = set(item.get('kpi_category', 'unknown') for item in kpi_data)
        response_parts.append(f"Categories: {', '.join(categories)}")

        return "\n".join(response_parts)


# Example usage
if __name__ == "__main__":
    print("KPI Query Tool loaded successfully")
