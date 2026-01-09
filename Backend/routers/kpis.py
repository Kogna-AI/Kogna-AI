"""
KPI Extraction System - API Router
===================================
This module provides REST API endpoints for accessing KPI metrics, including:
- Dashboard overview
- Agent performance metrics
- Connector-specific KPIs
- Time-series trend data
- User feedback submission
- Data export capabilities
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query, Response
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, date
from decimal import Decimal
import json
import csv
import io

from core.database import get_db
from core.kpi_models import (
    AgentPerformanceKPI,
    ConnectorKPI,
    UserEngagementKPI,
    KPIDashboard,
    KPITrendPoint,
    FeedbackSubmission,
    KPIExportParams,
    AgentPerformanceSummary,
    ConnectorKPITrend,
    ConnectorType,
    KPICategory
)
from auth.dependencies import get_backend_user_id
from psycopg2.extras import RealDictCursor

router = APIRouter(prefix="/api/kpis", tags=["KPIs"])


# ============================================================================
# Helper Functions
# ============================================================================

def calculate_date_range(days: int) -> tuple[datetime, datetime]:
    """Calculate start and end datetime from number of days"""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)
    return start_time, end_time


def serialize_decimal(obj):
    """Custom JSON serializer for Decimal objects"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


# ============================================================================
# Endpoint 1: GET /api/kpis/dashboard
# ============================================================================

@router.get("/dashboard", response_model=KPIDashboard)
def get_kpi_dashboard(
    days: int = Query(default=7, ge=1, le=365, description="Number of days to look back"),
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    user=Depends(get_backend_user_id),
    db=Depends(get_db)
):
    """
    Returns comprehensive KPI overview for the dashboard.

    - **days**: Number of days to include in metrics (default: 7)
    - **organization_id**: Optional filter (defaults to user's organization)

    Uses materialized views for fast response times.
    """
    # Use user's organization if not specified
    target_org_id = organization_id or user["organization_id"]

    # Security check: users can only access their own organization's data
    if target_org_id != user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only view KPIs for your own organization"
        )

    start_time, end_time = calculate_date_range(days)

    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # ===== Agent Performance KPIs =====
        cursor.execute("""
            SELECT
                COALESCE(AVG(avg_response_time_ms), 0) as avg_response_time_ms,
                COALESCE(SUM(execution_count), 0) as total_queries,
                COALESCE(SUM(total_cost_usd), 0) as total_cost_usd,
                COALESCE(AVG(success_rate_percent), 0) as success_rate
            FROM mv_agent_performance_summary
            WHERE organization_id = %s
                AND period_start >= %s
                AND period_end <= %s
        """, (target_org_id, start_time, end_time))

        agent_agg = cursor.fetchone()

        # Get per-agent breakdown
        cursor.execute("""
            SELECT
                agent_name,
                SUM(execution_count) as queries,
                AVG(avg_response_time_ms) as avg_response_time_ms,
                SUM(total_cost_usd) as cost_usd,
                AVG(success_rate_percent) as success_rate
            FROM mv_agent_performance_summary
            WHERE organization_id = %s
                AND period_start >= %s
                AND period_end <= %s
            GROUP BY agent_name
            ORDER BY queries DESC
        """, (target_org_id, start_time, end_time))

        by_agent = cursor.fetchall()

        agent_performance = AgentPerformanceKPI(
            avg_response_time_ms=float(agent_agg["avg_response_time_ms"] or 0),
            total_queries=int(agent_agg["total_queries"] or 0),
            total_cost_usd=Decimal(str(agent_agg["total_cost_usd"] or 0)),
            success_rate=float(agent_agg["success_rate"] or 0),
            by_agent=[dict(row) for row in by_agent]
        )

        # ===== Connector KPIs =====
        cursor.execute("""
            SELECT
                connector_type,
                COUNT(DISTINCT source_id) as total_syncs,
                COUNT(*) as total_kpis_extracted,
                MAX(last_extraction) as last_sync
            FROM mv_connector_kpi_trends
            WHERE organization_id = %s
                AND date >= %s::date
            GROUP BY connector_type
        """, (target_org_id, start_time))

        connector_rows = cursor.fetchall()
        connector_kpis = {}

        for row in connector_rows:
            connector_type = row["connector_type"]

            # Get KPIs by category for this connector
            cursor.execute("""
                SELECT kpi_category, COUNT(*) as count
                FROM mv_connector_kpi_trends
                WHERE organization_id = %s
                    AND connector_type = %s
                    AND date >= %s::date
                GROUP BY kpi_category
            """, (target_org_id, connector_type, start_time))

            kpis_by_category = {cat["kpi_category"]: cat["count"] for cat in cursor.fetchall()}

            connector_kpis[connector_type] = ConnectorKPI(
                connector_type=connector_type,
                total_syncs=row["total_syncs"],
                total_kpis_extracted=row["total_kpis_extracted"],
                last_sync=row["last_sync"],
                kpis_by_category=kpis_by_category
            )

        # ===== User Engagement KPIs =====
        cursor.execute("""
            SELECT
                COUNT(DISTINCT user_id) as active_users,
                AVG(avg_satisfaction_score) as avg_satisfaction,
                SUM(session_count) as total_sessions,
                SUM(query_count) as total_queries,
                AVG(total_session_duration_seconds::float / NULLIF(session_count, 0)) as avg_session_duration
            FROM user_engagement_metrics
            WHERE organization_id = %s
                AND date >= %s::date
                AND date <= %s::date
        """, (target_org_id, start_time, end_time))

        engagement = cursor.fetchone()

        user_engagement = UserEngagementKPI(
            active_users=int(engagement["active_users"] or 0),
            avg_satisfaction=Decimal(str(engagement["avg_satisfaction"] or 0)) if engagement["avg_satisfaction"] else None,
            total_sessions=int(engagement["total_sessions"] or 0),
            total_queries=int(engagement["total_queries"] or 0),
            avg_session_duration_seconds=float(engagement["avg_session_duration"] or 0)
        )

        return KPIDashboard(
            agent_performance=agent_performance,
            connector_kpis=connector_kpis,
            user_engagement=user_engagement,
            period_start=start_time,
            period_end=end_time
        )


# ============================================================================
# Endpoint 2: GET /api/kpis/agents/performance
# ============================================================================

@router.get("/agents/performance")
def get_agent_performance(
    agent_name: Optional[str] = Query(None, description="Filter by specific agent"),
    days: int = Query(default=7, ge=1, le=365, description="Number of days to look back"),
    group_by: str = Query(default="day", regex="^(hour|day|week)$", description="Grouping granularity"),
    user=Depends(get_backend_user_id),
    db=Depends(get_db)
):
    """
    Returns detailed agent-specific performance metrics.

    - **agent_name**: Optional filter for specific agent
    - **days**: Number of days to look back
    - **group_by**: Aggregation granularity (hour, day, week)

    Filters automatically by user's organization.
    """
    start_time, end_time = calculate_date_range(days)
    organization_id = user["organization_id"]

    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Build dynamic query based on grouping
        if group_by == "hour":
            time_column = "hour"
            order_by = "hour DESC"
        elif group_by == "week":
            time_column = "DATE_TRUNC('week', date)"
            order_by = "DATE_TRUNC('week', date) DESC"
        else:  # day
            time_column = "date"
            order_by = "date DESC"

        query = f"""
            SELECT
                {time_column} as period,
                agent_name,
                model_used,
                SUM(execution_count) as execution_count,
                SUM(successful_executions) as successful_executions,
                SUM(failed_executions) as failed_executions,
                AVG(avg_response_time_ms) as avg_response_time_ms,
                AVG(median_response_time_ms) as median_response_time_ms,
                MAX(p95_response_time_ms) as p95_response_time_ms,
                MAX(p99_response_time_ms) as p99_response_time_ms,
                MIN(min_response_time_ms) as min_response_time_ms,
                MAX(max_response_time_ms) as max_response_time_ms,
                SUM(total_tokens) as total_tokens,
                SUM(total_cost_usd) as total_cost_usd,
                AVG(success_rate_percent) as success_rate_percent,
                AVG(avg_confidence_score) as avg_confidence_score
            FROM mv_agent_performance_summary
            WHERE organization_id = %s
                AND period_start >= %s
                AND period_end <= %s
        """

        params = [organization_id, start_time, end_time]

        if agent_name:
            query += " AND agent_name = %s"
            params.append(agent_name)

        query += f" GROUP BY {time_column}, agent_name, model_used ORDER BY {order_by} LIMIT 1000"

        cursor.execute(query, params)
        results = cursor.fetchall()

        # Also get aggregates
        agg_query = """
            SELECT
                COUNT(*) as total_records,
                AVG(avg_response_time_ms) as overall_avg_response_time,
                SUM(total_cost_usd) as overall_total_cost,
                AVG(success_rate_percent) as overall_success_rate
            FROM mv_agent_performance_summary
            WHERE organization_id = %s
                AND period_start >= %s
                AND period_end <= %s
        """

        agg_params = [organization_id, start_time, end_time]
        if agent_name:
            agg_query += " AND agent_name = %s"
            agg_params.append(agent_name)

        cursor.execute(agg_query, agg_params)
        aggregates = cursor.fetchone()

        return {
            "success": True,
            "data": {
                "time_series": [dict(row) for row in results],
                "aggregates": dict(aggregates),
                "filters": {
                    "agent_name": agent_name,
                    "days": days,
                    "group_by": group_by,
                    "period_start": start_time.isoformat(),
                    "period_end": end_time.isoformat()
                }
            }
        }


# ============================================================================
# Endpoint 3: GET /api/kpis/connectors/{connector_type}
# ============================================================================

@router.get("/connectors/{connector_type}")
def get_connector_kpis(
    connector_type: ConnectorType,
    kpi_category: Optional[KPICategory] = Query(None, description="Filter by KPI category"),
    source_id: Optional[str] = Query(None, description="Filter by specific source ID"),
    days: int = Query(default=30, ge=1, le=365, description="Number of days to look back"),
    user=Depends(get_backend_user_id),
    db=Depends(get_db)
):
    """
    Returns KPIs for a specific connector type (jira, asana, etc.).

    - **connector_type**: The connector to query (jira, asana, google_drive, etc.)
    - **kpi_category**: Optional filter by category (velocity, burndown, etc.)
    - **source_id**: Optional filter by specific source (e.g., project ID)
    - **days**: Number of days to look back

    Returns latest values and trends.
    """
    start_time, end_time = calculate_date_range(days)
    organization_id = user["organization_id"]

    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Build dynamic query
        query = """
            SELECT
                date,
                kpi_name,
                kpi_category,
                kpi_unit,
                source_id,
                source_name,
                latest_kpi_value,
                sample_count,
                first_extraction,
                last_extraction,
                day_over_day_change,
                trend_direction,
                moving_avg_7day
            FROM mv_connector_kpi_trends
            WHERE organization_id = %s
                AND connector_type = %s
                AND date >= %s::date
        """

        params = [organization_id, connector_type.value, start_time]

        if kpi_category:
            query += " AND kpi_category = %s"
            params.append(kpi_category.value)

        if source_id:
            query += " AND source_id = %s"
            params.append(source_id)

        query += " ORDER BY date DESC, kpi_name LIMIT 500"

        cursor.execute(query, params)
        trends = cursor.fetchall()

        # Get latest values for quick overview
        latest_query = """
            SELECT DISTINCT ON (kpi_name)
                kpi_name,
                kpi_category,
                latest_kpi_value,
                kpi_unit,
                trend_direction,
                day_over_day_change,
                last_extraction
            FROM mv_connector_kpi_trends
            WHERE organization_id = %s
                AND connector_type = %s
                AND date >= %s::date
        """

        latest_params = [organization_id, connector_type.value, start_time]

        if kpi_category:
            latest_query += " AND kpi_category = %s"
            latest_params.append(kpi_category.value)

        if source_id:
            latest_query += " AND source_id = %s"
            latest_params.append(source_id)

        latest_query += " ORDER BY kpi_name, date DESC"

        cursor.execute(latest_query, latest_params)
        latest_values = cursor.fetchall()

        return {
            "success": True,
            "data": {
                "connector_type": connector_type.value,
                "latest_values": [dict(row) for row in latest_values],
                "trends": [dict(row) for row in trends],
                "filters": {
                    "kpi_category": kpi_category.value if kpi_category else None,
                    "source_id": source_id,
                    "days": days,
                    "period_start": start_time.isoformat(),
                    "period_end": end_time.isoformat()
                }
            }
        }


# ============================================================================
# Endpoint 4: GET /api/kpis/trends/{kpi_category}/{kpi_name}
# ============================================================================

@router.get("/trends/{kpi_category}/{kpi_name}")
def get_kpi_trends(
    kpi_category: KPICategory,
    kpi_name: str,
    connector_type: Optional[ConnectorType] = Query(None, description="Filter by connector type"),
    source_id: Optional[str] = Query(None, description="Filter by source ID"),
    days: int = Query(default=30, ge=1, le=365, description="Number of days to look back"),
    granularity: str = Query(default="day", regex="^(day|week|month)$", description="Time granularity"),
    user=Depends(get_backend_user_id),
    db=Depends(get_db)
):
    """
    Returns time-series data for charting a specific KPI.

    - **kpi_category**: The KPI category (velocity, burndown, etc.)
    - **kpi_name**: The specific KPI name
    - **connector_type**: Optional connector filter
    - **source_id**: Optional source filter
    - **days**: Number of days to look back
    - **granularity**: Time grouping (day, week, month)

    Returns array of {timestamp, value, metadata} for visualization.
    """
    start_time, end_time = calculate_date_range(days)
    organization_id = user["organization_id"]

    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Determine time grouping
        if granularity == "week":
            time_group = "DATE_TRUNC('week', date)"
        elif granularity == "month":
            time_group = "DATE_TRUNC('month', date)"
        else:
            time_group = "date"

        # Build query
        query = f"""
            SELECT
                {time_group} as timestamp,
                latest_kpi_value as value,
                kpi_unit,
                source_id,
                source_name,
                trend_direction,
                moving_avg_7day,
                day_over_day_change,
                sample_count
            FROM mv_connector_kpi_trends
            WHERE organization_id = %s
                AND kpi_category = %s
                AND kpi_name = %s
                AND date >= %s::date
        """

        params = [organization_id, kpi_category.value, kpi_name, start_time]

        if connector_type:
            query += " AND connector_type = %s"
            params.append(connector_type.value)

        if source_id:
            query += " AND source_id = %s"
            params.append(source_id)

        query += f" ORDER BY {time_group} ASC LIMIT 1000"

        cursor.execute(query, params)
        results = cursor.fetchall()

        # Transform to KPITrendPoint format
        trend_points = []
        for row in results:
            trend_points.append({
                "timestamp": row["timestamp"],
                "value": row["value"],
                "metadata": {
                    "kpi_unit": row["kpi_unit"],
                    "source_id": row["source_id"],
                    "source_name": row["source_name"],
                    "trend_direction": row["trend_direction"],
                    "moving_avg_7day": float(row["moving_avg_7day"]) if row["moving_avg_7day"] else None,
                    "day_over_day_change": float(row["day_over_day_change"]) if row["day_over_day_change"] else None,
                    "sample_count": row["sample_count"]
                }
            })

        return {
            "success": True,
            "data": {
                "kpi_category": kpi_category.value,
                "kpi_name": kpi_name,
                "granularity": granularity,
                "trend_points": trend_points,
                "count": len(trend_points),
                "filters": {
                    "connector_type": connector_type.value if connector_type else None,
                    "source_id": source_id,
                    "days": days,
                    "period_start": start_time.isoformat(),
                    "period_end": end_time.isoformat()
                }
            }
        }


# ============================================================================
# Endpoint 5: POST /api/kpis/feedback
# ============================================================================

@router.post("/feedback", status_code=status.HTTP_201_CREATED)
def submit_feedback(
    feedback: FeedbackSubmission,
    user=Depends(get_backend_user_id),
    db=Depends(get_db)
):
    """
    Submit user satisfaction feedback for a specific message.

    - **message_id**: The message to provide feedback on
    - **satisfaction_score**: Rating from 1-5
    - **feedback_text**: Optional text feedback

    Updates user_engagement_metrics and rag_quality_metrics tables.
    """
    user_id = user["user_id"]
    organization_id = user["organization_id"]

    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Update RAG quality metrics
        cursor.execute("""
            INSERT INTO rag_quality_metrics (user_id, message_id, user_satisfaction, created_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (message_id)
            DO UPDATE SET user_satisfaction = EXCLUDED.user_satisfaction
            RETURNING id
        """, (user_id, feedback.message_id, feedback.satisfaction_score))

        rag_metric_id = cursor.fetchone()["id"]

        # Update user engagement metrics for today
        today = date.today()

        cursor.execute("""
            INSERT INTO user_engagement_metrics
            (user_id, organization_id, date, feedback_count, avg_satisfaction_score, created_at, updated_at)
            VALUES (%s, %s, %s, 1, %s, NOW(), NOW())
            ON CONFLICT (user_id, date)
            DO UPDATE SET
                feedback_count = user_engagement_metrics.feedback_count + 1,
                avg_satisfaction_score = (
                    (COALESCE(user_engagement_metrics.avg_satisfaction_score, 0) * user_engagement_metrics.feedback_count + %s)
                    / (user_engagement_metrics.feedback_count + 1)
                ),
                updated_at = NOW()
            RETURNING id
        """, (user_id, organization_id, today, feedback.satisfaction_score, feedback.satisfaction_score))

        engagement_metric_id = cursor.fetchone()["id"]

        return {
            "success": True,
            "message": "Feedback submitted successfully",
            "data": {
                "rag_metric_id": rag_metric_id,
                "engagement_metric_id": engagement_metric_id,
                "message_id": feedback.message_id,
                "satisfaction_score": feedback.satisfaction_score
            }
        }


# ============================================================================
# Endpoint 6: GET /api/kpis/export
# ============================================================================

@router.get("/export")
def export_kpis(
    format: str = Query(default="json", regex="^(json|csv)$", description="Export format"),
    kpi_types: Optional[str] = Query(None, description="Comma-separated list: agent,connector,engagement"),
    date_range_start: Optional[datetime] = Query(None, description="Start date for export"),
    date_range_end: Optional[datetime] = Query(None, description="End date for export"),
    user=Depends(get_backend_user_id),
    db=Depends(get_db)
):
    """
    Export KPIs as CSV or JSON for reporting and BI integration.

    - **format**: Output format (json or csv)
    - **kpi_types**: Which KPIs to include (agent, connector, engagement)
    - **date_range_start**: Start date (defaults to 30 days ago)
    - **date_range_end**: End date (defaults to now)

    Rate limited to prevent abuse.
    """
    organization_id = user["organization_id"]

    # Default date range: last 30 days
    if not date_range_end:
        date_range_end = datetime.utcnow()
    if not date_range_start:
        date_range_start = date_range_end - timedelta(days=30)

    # Parse KPI types
    requested_types = set(kpi_types.split(",")) if kpi_types else {"agent", "connector", "engagement"}

    export_data = {}

    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Export Agent Performance
        if "agent" in requested_types:
            cursor.execute("""
                SELECT *
                FROM mv_agent_performance_summary
                WHERE organization_id = %s
                    AND period_start >= %s
                    AND period_end <= %s
                ORDER BY date DESC, hour DESC
                LIMIT 10000
            """, (organization_id, date_range_start, date_range_end))

            export_data["agent_performance"] = [dict(row) for row in cursor.fetchall()]

        # Export Connector KPIs
        if "connector" in requested_types:
            cursor.execute("""
                SELECT *
                FROM mv_connector_kpi_trends
                WHERE organization_id = %s
                    AND date >= %s::date
                    AND date <= %s::date
                ORDER BY date DESC
                LIMIT 10000
            """, (organization_id, date_range_start, date_range_end))

            export_data["connector_kpis"] = [dict(row) for row in cursor.fetchall()]

        # Export User Engagement
        if "engagement" in requested_types:
            cursor.execute("""
                SELECT *
                FROM user_engagement_metrics
                WHERE organization_id = %s
                    AND date >= %s::date
                    AND date <= %s::date
                ORDER BY date DESC
                LIMIT 10000
            """, (organization_id, date_range_start, date_range_end))

            export_data["user_engagement"] = [dict(row) for row in cursor.fetchall()]

    # Format response based on requested format
    if format == "csv":
        # Create CSV output
        output = io.StringIO()

        # Write each KPI type to separate sections
        for kpi_type, records in export_data.items():
            if not records:
                continue

            output.write(f"\n# {kpi_type.upper()}\n")

            if records:
                writer = csv.DictWriter(output, fieldnames=records[0].keys())
                writer.writeheader()
                writer.writerows(records)

            output.write("\n")

        # Return as downloadable file
        csv_content = output.getvalue()
        output.close()

        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=kpi_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )

    else:  # JSON format
        return {
            "success": True,
            "export_metadata": {
                "organization_id": organization_id,
                "date_range_start": date_range_start.isoformat(),
                "date_range_end": date_range_end.isoformat(),
                "kpi_types": list(requested_types),
                "exported_at": datetime.utcnow().isoformat(),
                "record_counts": {k: len(v) for k, v in export_data.items()}
            },
            "data": export_data
        }


# ============================================================================
# Health Check Endpoint
# ============================================================================

@router.get("/health")
def kpi_health_check(db=Depends(get_db)):
    """Check KPI system health and materialized view freshness"""
    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Check materialized view freshness
        cursor.execute("""
            SELECT
                MAX(last_refreshed) as agent_last_refresh
            FROM mv_agent_performance_summary
        """)
        agent_refresh = cursor.fetchone()

        cursor.execute("""
            SELECT
                MAX(last_refreshed) as connector_last_refresh
            FROM mv_connector_kpi_trends
        """)
        connector_refresh = cursor.fetchone()

        # Check record counts
        cursor.execute("SELECT COUNT(*) as count FROM agent_performance_metrics")
        agent_count = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM connector_kpis")
        connector_count = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM user_engagement_metrics")
        engagement_count = cursor.fetchone()["count"]

        return {
            "success": True,
            "status": "healthy",
            "materialized_views": {
                "agent_performance_last_refresh": agent_refresh["agent_last_refresh"],
                "connector_kpi_last_refresh": connector_refresh["connector_last_refresh"]
            },
            "record_counts": {
                "agent_performance_metrics": agent_count,
                "connector_kpis": connector_count,
                "user_engagement_metrics": engagement_count
            },
            "checked_at": datetime.utcnow().isoformat()
        }


# ============================================================================
# Scheduler Endpoints (Phase 5)
# ============================================================================

@router.get("/scheduler/status")
def get_scheduler_status():
    """
    Get current scheduler status and job information.

    Returns information about:
    - Scheduler running state
    - Registered jobs and their next run times
    - Recent execution logs
    """
    try:
        from services.kpi_scheduler import get_scheduler_status

        # Get scheduler status
        status_info = get_scheduler_status()

        # Get recent execution logs from database
        from supabase_connect import get_supabase_manager
        supabase = get_supabase_manager().client

        logs_response = supabase.table("scheduler_logs") \
            .select("*") \
            .order("executed_at", desc=True) \
            .limit(20) \
            .execute()

        recent_logs = logs_response.data if logs_response.data else []

        return {
            "success": True,
            "scheduler": status_info,
            "recent_executions": recent_logs,
            "checked_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "scheduler": {"status": "error"},
            "checked_at": datetime.utcnow().isoformat()
        }


@router.post("/scheduler/trigger/{task_name}")
async def trigger_scheduler_task(
    task_name: str,
    user=Depends(get_backend_user_id)
):
    """
    Manually trigger a scheduled task for testing or on-demand execution.

    Available tasks:
    - refresh_views: Refresh materialized views
    - daily_engagement: Aggregate daily engagement metrics
    - weekly_report: Generate weekly KPI report
    - cleanup: Clean up old metrics

    Requires authentication. Returns task execution results.
    """
    # Only allow admin users to trigger tasks (you can add role checking here)
    # For now, any authenticated user can trigger

    try:
        from services import kpi_scheduler

        if task_name == "refresh_views":
            result = await kpi_scheduler.trigger_refresh_views()
        elif task_name == "daily_engagement":
            result = await kpi_scheduler.trigger_daily_engagement()
        elif task_name == "weekly_report":
            result = await kpi_scheduler.trigger_weekly_report()
        elif task_name == "cleanup":
            result = await kpi_scheduler.trigger_cleanup()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown task: {task_name}. Valid tasks: refresh_views, daily_engagement, weekly_report, cleanup"
            )

        return {
            "success": True,
            "task_name": task_name,
            "result": result,
            "triggered_at": datetime.utcnow().isoformat(),
            "triggered_by": user["user_id"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger task: {str(e)}"
        )
