"""
KPI Scheduler - Phase 5: Scheduled Reporting System
====================================================
This module manages scheduled tasks for KPI data processing and reporting:
- Hourly materialized view refreshes
- Daily engagement metric aggregation
- Weekly KPI report generation
- Periodic metric cleanup

Uses APScheduler for task orchestration with error handling and retry logic.
"""

import asyncio
import logging
from datetime import datetime, timedelta, time as datetime_time
from typing import Optional, Dict, List, Any
import json
from decimal import Decimal

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from supabase_connect import get_supabase_manager
from psycopg2.extras import RealDictCursor
import psycopg2

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Supabase client
supabase = get_supabase_manager().client

# Global scheduler instance
_scheduler: Optional[AsyncIOScheduler] = None


# ============================================================================
# Database Connection Helper
# ============================================================================

def get_postgres_connection():
    """
    Creates a direct PostgreSQL connection for executing functions
    and operations not available through Supabase Python client
    """
    import os
    from urllib.parse import urlparse

    # Parse Supabase URL to get PostgreSQL connection string
    supabase_url = os.getenv("SUPABASE_URL")
    db_password = os.getenv("SUPABASE_DB_PASSWORD")

    if not db_password:
        raise ValueError("SUPABASE_DB_PASSWORD not set in environment")

    # Parse URL to get host
    parsed = urlparse(supabase_url)
    host = parsed.hostname

    # Construct PostgreSQL connection string
    # Supabase uses port 5432 for direct PostgreSQL connections
    conn_string = f"postgresql://postgres:{db_password}@{host}:5432/postgres"

    return psycopg2.connect(conn_string)


# ============================================================================
# Task 1: Refresh Materialized Views (Hourly)
# ============================================================================

async def refresh_materialized_views():
    """
    Refreshes all KPI materialized views to keep dashboard data up-to-date.

    Views refreshed:
    - mv_agent_performance_summary
    - mv_connector_kpi_trends

    Runs: Every hour
    Duration: ~1-5 seconds depending on data volume
    """
    start_time = datetime.utcnow()
    logger.info("=" * 60)
    logger.info("Starting materialized view refresh")
    logger.info(f"Started at: {start_time.isoformat()}")

    views_refreshed = []
    errors = []

    try:
        # Use PostgreSQL connection for REFRESH MATERIALIZED VIEW command
        conn = get_postgres_connection()
        cursor = conn.cursor()

        # Refresh agent performance summary view
        try:
            logger.info("Refreshing mv_agent_performance_summary...")
            cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_agent_performance_summary")
            conn.commit()
            views_refreshed.append("mv_agent_performance_summary")
            logger.info("✓ mv_agent_performance_summary refreshed")
        except Exception as e:
            error_msg = f"Failed to refresh mv_agent_performance_summary: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            conn.rollback()

        # Refresh connector KPI trends view
        try:
            logger.info("Refreshing mv_connector_kpi_trends...")
            cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_connector_kpi_trends")
            conn.commit()
            views_refreshed.append("mv_connector_kpi_trends")
            logger.info("✓ mv_connector_kpi_trends refreshed")
        except Exception as e:
            error_msg = f"Failed to refresh mv_connector_kpi_trends: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            conn.rollback()

        cursor.close()
        conn.close()

    except Exception as e:
        error_msg = f"Database connection failed: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)

    # Calculate duration
    end_time = datetime.utcnow()
    duration_ms = int((end_time - start_time).total_seconds() * 1000)

    # Log execution to scheduler_logs table
    try:
        log_data = {
            "task_name": "refresh_materialized_views",
            "status": "success" if not errors else "partial_failure" if views_refreshed else "failed",
            "execution_time_ms": duration_ms,
            "details": {
                "views_refreshed": views_refreshed,
                "errors": errors,
                "started_at": start_time.isoformat(),
                "completed_at": end_time.isoformat()
            }
        }

        supabase.table("scheduler_logs").insert(log_data).execute()

    except Exception as e:
        logger.error(f"Failed to log scheduler execution: {e}")

    logger.info(f"Materialized view refresh completed in {duration_ms}ms")
    logger.info(f"Views refreshed: {len(views_refreshed)}/{2}")
    if errors:
        logger.warning(f"Errors encountered: {len(errors)}")
    logger.info("=" * 60)

    return {
        "views_refreshed": views_refreshed,
        "duration_ms": duration_ms,
        "errors": errors
    }


# ============================================================================
# Task 2: Aggregate Daily Engagement (Daily at 1 AM)
# ============================================================================

async def aggregate_daily_engagement():
    """
    Aggregates previous day's user engagement metrics.

    Calculates:
    - Session counts and durations per user
    - Query/message counts
    - Active time windows
    - Top conversation topics

    Runs: Daily at 1:00 AM UTC
    Duration: ~5-30 seconds depending on chat volume
    """
    start_time = datetime.utcnow()
    logger.info("=" * 60)
    logger.info("Starting daily engagement aggregation")
    logger.info(f"Started at: {start_time.isoformat()}")

    # Calculate previous day's date range
    yesterday = (datetime.utcnow() - timedelta(days=1)).date()
    period_start = datetime.combine(yesterday, datetime_time.min)
    period_end = datetime.combine(yesterday, datetime_time.max)

    logger.info(f"Aggregating data for: {yesterday.isoformat()}")

    users_processed = 0
    total_metrics_saved = 0
    errors = []

    try:
        # Get all organizations
        orgs_response = supabase.table("organizations").select("id").execute()
        organizations = orgs_response.data if orgs_response.data else []

        for org in organizations:
            org_id = org["id"]

            try:
                # Get all users in organization
                users_response = supabase.table("users") \
                    .select("id") \
                    .eq("organization_id", org_id) \
                    .execute()

                users = users_response.data if users_response.data else []

                for user in users:
                    user_id = user["id"]

                    try:
                        # Query chat messages for the user on this date
                        messages_response = supabase.table("chat_messages") \
                            .select("*") \
                            .eq("user_id", user_id) \
                            .gte("created_at", period_start.isoformat()) \
                            .lte("created_at", period_end.isoformat()) \
                            .execute()

                        messages = messages_response.data if messages_response.data else []

                        if not messages:
                            continue  # Skip users with no activity

                        # Calculate metrics
                        total_queries = len([m for m in messages if m.get("role") == "user"])
                        total_responses = len([m for m in messages if m.get("role") == "assistant"])

                        # Estimate session count by grouping messages within 30-minute windows
                        session_count = 1
                        last_timestamp = None
                        for msg in sorted(messages, key=lambda x: x["created_at"]):
                            msg_time = datetime.fromisoformat(msg["created_at"].replace("Z", "+00:00"))
                            if last_timestamp:
                                if (msg_time - last_timestamp).total_seconds() > 1800:  # 30 minutes
                                    session_count += 1
                            last_timestamp = msg_time

                        # Calculate average session duration (simplified)
                        if messages:
                            first_msg = min(messages, key=lambda x: x["created_at"])
                            last_msg = max(messages, key=lambda x: x["created_at"])
                            first_time = datetime.fromisoformat(first_msg["created_at"].replace("Z", "+00:00"))
                            last_time = datetime.fromisoformat(last_msg["created_at"].replace("Z", "+00:00"))
                            total_duration_seconds = (last_time - first_time).total_seconds()
                            avg_session_duration_seconds = int(total_duration_seconds / session_count) if session_count > 0 else 0
                        else:
                            avg_session_duration_seconds = 0

                        # Extract top topics from message content (simplified - top 3 keywords)
                        all_text = " ".join([m.get("content", "") for m in messages if m.get("content")])
                        words = all_text.lower().split()
                        # Filter common words and count frequency
                        common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "i", "you", "he", "she", "it", "we", "they"}
                        word_counts = {}
                        for word in words:
                            if len(word) > 3 and word not in common_words:
                                word_counts[word] = word_counts.get(word, 0) + 1

                        top_topics = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:3]
                        top_topics_list = [word for word, count in top_topics]

                        # Insert engagement metrics
                        engagement_data = {
                            "user_id": user_id,
                            "organization_id": org_id,
                            "date": yesterday.isoformat(),
                            "session_count": session_count,
                            "total_queries": total_queries,
                            "total_responses": total_responses,
                            "avg_session_duration_seconds": avg_session_duration_seconds,
                            "top_topics": top_topics_list,
                            "period_start": period_start.isoformat(),
                            "period_end": period_end.isoformat()
                        }

                        supabase.table("user_engagement_metrics").upsert(
                            engagement_data,
                            on_conflict="user_id,date"
                        ).execute()

                        total_metrics_saved += 1
                        users_processed += 1

                    except Exception as e:
                        error_msg = f"Failed to process user {user_id}: {str(e)}"
                        logger.error(error_msg)
                        errors.append(error_msg)

            except Exception as e:
                error_msg = f"Failed to process organization {org_id}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

    except Exception as e:
        error_msg = f"Failed to fetch organizations: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)

    # Calculate duration
    end_time = datetime.utcnow()
    duration_ms = int((end_time - start_time).total_seconds() * 1000)

    # Log execution
    try:
        log_data = {
            "task_name": "aggregate_daily_engagement",
            "status": "success" if not errors else "partial_failure" if users_processed > 0 else "failed",
            "execution_time_ms": duration_ms,
            "details": {
                "date": yesterday.isoformat(),
                "users_processed": users_processed,
                "metrics_saved": total_metrics_saved,
                "errors": errors[:10],  # Limit error list
                "started_at": start_time.isoformat(),
                "completed_at": end_time.isoformat()
            }
        }

        supabase.table("scheduler_logs").insert(log_data).execute()

    except Exception as e:
        logger.error(f"Failed to log scheduler execution: {e}")

    logger.info(f"Daily engagement aggregation completed in {duration_ms}ms")
    logger.info(f"Users processed: {users_processed}")
    logger.info(f"Metrics saved: {total_metrics_saved}")
    if errors:
        logger.warning(f"Errors encountered: {len(errors)}")
    logger.info("=" * 60)

    return {
        "users_processed": users_processed,
        "metrics_saved": total_metrics_saved,
        "duration_ms": duration_ms,
        "errors": errors
    }


# ============================================================================
# Task 3: Generate Weekly KPI Report (Monday at 9 AM)
# ============================================================================

async def generate_weekly_kpi_report():
    """
    Generates comprehensive weekly KPI report per organization.

    Includes:
    - Agent performance summary (response times, costs, success rates)
    - Top connector KPIs (Jira, Asana, etc.)
    - User engagement trends
    - Quality metrics

    Saves report as JSON to Supabase Storage.
    Future: PDF generation and email notifications.

    Runs: Every Monday at 9:00 AM UTC
    Duration: ~10-60 seconds depending on data volume
    """
    start_time = datetime.utcnow()
    logger.info("=" * 60)
    logger.info("Starting weekly KPI report generation")
    logger.info(f"Started at: {start_time.isoformat()}")

    # Calculate previous week's date range (Monday to Sunday)
    today = datetime.utcnow().date()
    # Find last Monday (7 days ago if today is Monday, otherwise find previous Monday)
    days_since_monday = (today.weekday() + 7) % 7  # 0 = Monday
    if days_since_monday == 0:
        days_since_monday = 7  # If today is Monday, go back to last Monday

    week_end = today - timedelta(days=days_since_monday)  # Last Sunday
    week_start = week_end - timedelta(days=6)  # Previous Monday

    period_start = datetime.combine(week_start, datetime_time.min)
    period_end = datetime.combine(week_end, datetime_time.max)

    logger.info(f"Report period: {week_start.isoformat()} to {week_end.isoformat()}")

    reports_generated = 0
    errors = []

    try:
        # Get all organizations
        orgs_response = supabase.table("organizations").select("id, name").execute()
        organizations = orgs_response.data if orgs_response.data else []

        for org in organizations:
            org_id = org["id"]
            org_name = org.get("name", "Unknown Organization")

            logger.info(f"Generating report for: {org_name} ({org_id})")

            try:
                report = {
                    "organization_id": org_id,
                    "organization_name": org_name,
                    "report_type": "weekly_kpi_summary",
                    "period_start": period_start.isoformat(),
                    "period_end": period_end.isoformat(),
                    "generated_at": datetime.utcnow().isoformat(),
                    "sections": {}
                }

                # Section 1: Agent Performance Summary
                try:
                    conn = get_postgres_connection()
                    cursor = conn.cursor(cursor_factory=RealDictCursor)

                    cursor.execute("""
                        SELECT
                            agent_name,
                            COALESCE(AVG(avg_response_time_ms), 0) as avg_response_time_ms,
                            COALESCE(SUM(execution_count), 0) as total_executions,
                            COALESCE(SUM(total_cost_usd), 0) as total_cost_usd,
                            COALESCE(AVG(success_rate_percent), 0) as success_rate_percent
                        FROM mv_agent_performance_summary
                        WHERE organization_id = %s
                            AND date >= %s::date
                            AND date <= %s::date
                        GROUP BY agent_name
                        ORDER BY total_executions DESC
                    """, (org_id, week_start, week_end))

                    agent_performance = [dict(row) for row in cursor.fetchall()]

                    # Convert Decimal to float for JSON serialization
                    for row in agent_performance:
                        for key, value in row.items():
                            if isinstance(value, Decimal):
                                row[key] = float(value)

                    report["sections"]["agent_performance"] = {
                        "total_agents": len(agent_performance),
                        "agents": agent_performance
                    }

                    cursor.close()
                    conn.close()

                except Exception as e:
                    logger.error(f"Failed to fetch agent performance: {e}")
                    report["sections"]["agent_performance"] = {"error": str(e)}

                # Section 2: Top Connector KPIs
                try:
                    conn = get_postgres_connection()
                    cursor = conn.cursor(cursor_factory=RealDictCursor)

                    cursor.execute("""
                        SELECT
                            connector_type,
                            kpi_category,
                            kpi_name,
                            COALESCE(AVG(latest_value::float), 0) as avg_value,
                            COUNT(*) as data_points
                        FROM mv_connector_kpi_trends
                        WHERE organization_id = %s
                            AND date >= %s::date
                            AND date <= %s::date
                        GROUP BY connector_type, kpi_category, kpi_name
                        ORDER BY connector_type, kpi_category, kpi_name
                    """, (org_id, week_start, week_end))

                    connector_kpis = [dict(row) for row in cursor.fetchall()]

                    # Convert Decimal to float
                    for row in connector_kpis:
                        for key, value in row.items():
                            if isinstance(value, Decimal):
                                row[key] = float(value)

                    # Group by connector type
                    kpis_by_connector = {}
                    for kpi in connector_kpis:
                        connector = kpi["connector_type"]
                        if connector not in kpis_by_connector:
                            kpis_by_connector[connector] = []
                        kpis_by_connector[connector].append(kpi)

                    report["sections"]["connector_kpis"] = {
                        "total_connectors": len(kpis_by_connector),
                        "connectors": kpis_by_connector
                    }

                    cursor.close()
                    conn.close()

                except Exception as e:
                    logger.error(f"Failed to fetch connector KPIs: {e}")
                    report["sections"]["connector_kpis"] = {"error": str(e)}

                # Section 3: User Engagement Trends
                try:
                    engagement_response = supabase.table("user_engagement_metrics") \
                        .select("*") \
                        .eq("organization_id", org_id) \
                        .gte("date", week_start.isoformat()) \
                        .lte("date", week_end.isoformat()) \
                        .execute()

                    engagement_data = engagement_response.data if engagement_response.data else []

                    # Calculate aggregates
                    total_sessions = sum(e.get("session_count", 0) for e in engagement_data)
                    total_queries = sum(e.get("total_queries", 0) for e in engagement_data)
                    active_users = len(set(e["user_id"] for e in engagement_data))

                    report["sections"]["user_engagement"] = {
                        "active_users": active_users,
                        "total_sessions": total_sessions,
                        "total_queries": total_queries,
                        "avg_queries_per_user": round(total_queries / active_users, 2) if active_users > 0 else 0,
                        "daily_breakdown": engagement_data[:50]  # Limit to 50 records
                    }

                except Exception as e:
                    logger.error(f"Failed to fetch engagement data: {e}")
                    report["sections"]["user_engagement"] = {"error": str(e)}

                # Section 4: Quality Metrics (placeholder for future)
                report["sections"]["quality_metrics"] = {
                    "note": "Quality metrics to be implemented in future phase",
                    "planned_metrics": [
                        "Average user feedback score",
                        "Response accuracy rate",
                        "Issue resolution time"
                    ]
                }

                # Save report to Supabase Storage as JSON
                try:
                    report_json = json.dumps(report, indent=2, default=str)
                    report_filename = f"weekly_kpi_reports/{org_id}/{week_start.isoformat()}_to_{week_end.isoformat()}.json"

                    # Upload to Supabase Storage
                    supabase.storage.from_("kpi-reports").upload(
                        report_filename,
                        report_json.encode('utf-8'),
                        {"content-type": "application/json", "upsert": "true"}
                    )

                    logger.info(f"✓ Report saved: {report_filename}")
                    reports_generated += 1

                    # Also save metadata to database
                    report_metadata = {
                        "organization_id": org_id,
                        "report_type": "weekly_kpi_summary",
                        "period_start": period_start.isoformat(),
                        "period_end": period_end.isoformat(),
                        "file_path": report_filename,
                        "generated_at": datetime.utcnow().isoformat(),
                        "summary": {
                            "agents": report["sections"].get("agent_performance", {}).get("total_agents", 0),
                            "connectors": report["sections"].get("connector_kpis", {}).get("total_connectors", 0),
                            "active_users": report["sections"].get("user_engagement", {}).get("active_users", 0)
                        }
                    }

                    supabase.table("kpi_reports").insert(report_metadata).execute()

                except Exception as e:
                    error_msg = f"Failed to save report for {org_name}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            except Exception as e:
                error_msg = f"Failed to generate report for {org_name}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

    except Exception as e:
        error_msg = f"Failed to fetch organizations: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)

    # Calculate duration
    end_time = datetime.utcnow()
    duration_ms = int((end_time - start_time).total_seconds() * 1000)

    # Log execution
    try:
        log_data = {
            "task_name": "generate_weekly_kpi_report",
            "status": "success" if not errors else "partial_failure" if reports_generated > 0 else "failed",
            "execution_time_ms": duration_ms,
            "details": {
                "week_start": week_start.isoformat(),
                "week_end": week_end.isoformat(),
                "reports_generated": reports_generated,
                "errors": errors[:10],
                "started_at": start_time.isoformat(),
                "completed_at": end_time.isoformat()
            }
        }

        supabase.table("scheduler_logs").insert(log_data).execute()

    except Exception as e:
        logger.error(f"Failed to log scheduler execution: {e}")

    logger.info(f"Weekly KPI report generation completed in {duration_ms}ms")
    logger.info(f"Reports generated: {reports_generated}")
    if errors:
        logger.warning(f"Errors encountered: {len(errors)}")
    logger.info("=" * 60)

    return {
        "reports_generated": reports_generated,
        "duration_ms": duration_ms,
        "errors": errors
    }


# ============================================================================
# Task 4: Cleanup Old Metrics (Weekly on Sunday)
# ============================================================================

async def cleanup_old_metrics():
    """
    Archives and cleans up old metric data to maintain performance.

    Retention policy:
    - connector_kpis: Keep 90 days
    - user_engagement_metrics: Keep 90 days
    - agent_execution_logs: Keep 30 days
    - scheduler_logs: Keep 30 days

    Runs: Every Sunday at 3:00 AM UTC
    Duration: ~5-30 seconds depending on data volume
    """
    start_time = datetime.utcnow()
    logger.info("=" * 60)
    logger.info("Starting metric cleanup")
    logger.info(f"Started at: {start_time.isoformat()}")

    # Define retention policies (days)
    retention_policies = {
        "connector_kpis": 90,
        "user_engagement_metrics": 90,
        "agent_execution_logs": 30,
        "scheduler_logs": 30
    }

    tables_cleaned = []
    total_rows_deleted = 0
    errors = []

    try:
        conn = get_postgres_connection()
        cursor = conn.cursor()

        for table_name, retention_days in retention_policies.items():
            try:
                cutoff_date = (datetime.utcnow() - timedelta(days=retention_days)).date()

                logger.info(f"Cleaning {table_name} (keeping data after {cutoff_date.isoformat()})...")

                # Determine the timestamp column name (varies by table)
                if table_name == "connector_kpis":
                    timestamp_col = "extracted_at"
                elif table_name == "user_engagement_metrics":
                    timestamp_col = "date"
                elif table_name == "agent_execution_logs":
                    timestamp_col = "executed_at"
                elif table_name == "scheduler_logs":
                    timestamp_col = "executed_at"
                else:
                    timestamp_col = "created_at"

                # Delete old records
                delete_query = f"""
                    DELETE FROM {table_name}
                    WHERE {timestamp_col} < %s::date
                """

                cursor.execute(delete_query, (cutoff_date,))
                rows_deleted = cursor.rowcount
                conn.commit()

                tables_cleaned.append(table_name)
                total_rows_deleted += rows_deleted

                logger.info(f"✓ {table_name}: Deleted {rows_deleted} old records")

            except Exception as e:
                error_msg = f"Failed to clean {table_name}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                conn.rollback()

        cursor.close()
        conn.close()

        # Run VACUUM ANALYZE to reclaim space and update statistics
        try:
            logger.info("Running VACUUM ANALYZE to optimize tables...")
            conn = get_postgres_connection()
            conn.set_isolation_level(0)  # AUTOCOMMIT mode required for VACUUM
            cursor = conn.cursor()

            for table_name in tables_cleaned:
                cursor.execute(f"VACUUM ANALYZE {table_name}")
                logger.info(f"✓ Optimized {table_name}")

            cursor.close()
            conn.close()

        except Exception as e:
            logger.warning(f"VACUUM ANALYZE failed (non-critical): {e}")

    except Exception as e:
        error_msg = f"Database connection failed: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)

    # Calculate duration
    end_time = datetime.utcnow()
    duration_ms = int((end_time - start_time).total_seconds() * 1000)

    # Log execution
    try:
        log_data = {
            "task_name": "cleanup_old_metrics",
            "status": "success" if not errors else "partial_failure" if tables_cleaned else "failed",
            "execution_time_ms": duration_ms,
            "details": {
                "tables_cleaned": tables_cleaned,
                "total_rows_deleted": total_rows_deleted,
                "retention_policies": retention_policies,
                "errors": errors,
                "started_at": start_time.isoformat(),
                "completed_at": end_time.isoformat()
            }
        }

        supabase.table("scheduler_logs").insert(log_data).execute()

    except Exception as e:
        logger.error(f"Failed to log scheduler execution: {e}")

    logger.info(f"Metric cleanup completed in {duration_ms}ms")
    logger.info(f"Tables cleaned: {len(tables_cleaned)}/{len(retention_policies)}")
    logger.info(f"Total rows deleted: {total_rows_deleted}")
    if errors:
        logger.warning(f"Errors encountered: {len(errors)}")
    logger.info("=" * 60)

    return {
        "tables_cleaned": tables_cleaned,
        "rows_deleted": total_rows_deleted,
        "duration_ms": duration_ms,
        "errors": errors
    }


# ============================================================================
# Task 5: Cleanup Orphaned KPI Embeddings (Daily at 2 AM)
# ============================================================================

async def cleanup_orphaned_kpi_embeddings():
    """
    Removes KPI embeddings that no longer have corresponding KPI records.

    This happens when:
    - KPIs are deleted from connector_kpis table
    - Sources are disconnected or removed
    - Old embeddings weren't cleaned up properly

    Also removes KPI embeddings older than 90 days as a safety net.

    Runs: Daily at 2:00 AM UTC
    Duration: ~5-10 seconds
    """
    start_time = datetime.utcnow()
    logger.info("=" * 60)
    logger.info("Starting orphaned KPI embedding cleanup")
    logger.info(f"Started at: {start_time.isoformat()}")

    orphaned_deleted = 0
    old_deleted = 0
    errors = []

    try:
        conn = get_postgres_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # =====================================================================
        # STEP 1: Delete orphaned KPI embeddings (no matching KPI record)
        # =====================================================================

        logger.info("Finding orphaned KPI embeddings...")

        try:
            # Find KPI embeddings that don't have a matching KPI in connector_kpis
            orphaned_query = """
                DELETE FROM document_chunks
                WHERE file_path LIKE 'kpi://%'
                AND (metadata->>'kpi_id')::int NOT IN (
                    SELECT id FROM connector_kpis
                )
                RETURNING id
            """

            cursor.execute(orphaned_query)
            orphaned_deleted = cursor.rowcount
            conn.commit()

            logger.info(f"Deleted {orphaned_deleted} orphaned KPI embeddings")

        except Exception as e:
            error_msg = f"Failed to delete orphaned embeddings: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            conn.rollback()

        # =====================================================================
        # STEP 2: Delete KPI embeddings older than 90 days
        # =====================================================================

        logger.info("Deleting KPI embeddings older than 90 days...")

        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=90)).date()

            old_kpi_query = """
                DELETE FROM document_chunks
                WHERE file_path LIKE 'kpi://%'
                AND (metadata->>'extracted_at')::date < %s
                RETURNING id
            """

            cursor.execute(old_kpi_query, (cutoff_date,))
            old_deleted = cursor.rowcount
            conn.commit()

            logger.info(f"Deleted {old_deleted} old KPI embeddings (>90 days)")

        except Exception as e:
            error_msg = f"Failed to delete old KPI embeddings: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            conn.rollback()

        cursor.close()
        conn.close()

    except Exception as e:
        error_msg = f"Database connection failed: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)

    # Calculate duration
    end_time = datetime.utcnow()
    duration_ms = int((end_time - start_time).total_seconds() * 1000)

    total_deleted = orphaned_deleted + old_deleted

    # Log execution
    try:
        log_data = {
            "task_name": "cleanup_orphaned_kpi_embeddings",
            "status": "success" if not errors else "failed",
            "execution_time_ms": duration_ms,
            "details": {
                "orphaned_deleted": orphaned_deleted,
                "old_deleted": old_deleted,
                "total_deleted": total_deleted,
                "errors": errors,
                "started_at": start_time.isoformat(),
                "completed_at": end_time.isoformat()
            }
        }

        supabase.table("scheduler_logs").insert(log_data).execute()

    except Exception as e:
        logger.error(f"Failed to log scheduler execution: {e}")

    logger.info(f"KPI embedding cleanup completed in {duration_ms}ms")
    logger.info(f"Orphaned embeddings deleted: {orphaned_deleted}")
    logger.info(f"Old embeddings deleted: {old_deleted}")
    logger.info(f"Total deleted: {total_deleted}")
    if errors:
        logger.warning(f"Errors encountered: {len(errors)}")
    logger.info("=" * 60)

    return {
        "orphaned_deleted": orphaned_deleted,
        "old_deleted": old_deleted,
        "total_deleted": total_deleted,
        "duration_ms": duration_ms,
        "errors": errors
    }


# ============================================================================
# Scheduler Management
# ============================================================================

def job_listener(event):
    """
    Listens to job execution events for monitoring and debugging.
    """
    if event.exception:
        logger.error(f"Job {event.job_id} failed with exception: {event.exception}")
    else:
        logger.info(f"Job {event.job_id} executed successfully")


async def run_kpi_scheduler():
    """
    Initializes and starts the APScheduler with all KPI tasks.

    Scheduled Tasks:
    1. refresh_materialized_views() - Every hour
    2. aggregate_daily_engagement() - Daily at 1:00 AM UTC
    3. generate_weekly_kpi_report() - Every Monday at 9:00 AM UTC
    4. cleanup_old_metrics() - Every Sunday at 3:00 AM UTC
    """
    global _scheduler

    if _scheduler is not None:
        logger.warning("Scheduler already running, skipping initialization")
        return

    logger.info("=" * 60)
    logger.info("Initializing KPI Scheduler")
    logger.info("=" * 60)

    # Create scheduler
    _scheduler = AsyncIOScheduler()

    # Add event listener
    _scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    # Task 1: Refresh materialized views every hour
    _scheduler.add_job(
        refresh_materialized_views,
        trigger=IntervalTrigger(hours=1),
        id="refresh_materialized_views",
        name="Refresh Materialized Views",
        replace_existing=True,
        max_instances=1,
        coalesce=True
    )
    logger.info("✓ Scheduled: refresh_materialized_views (hourly)")

    # Task 2: Aggregate daily engagement at 1:00 AM UTC
    _scheduler.add_job(
        aggregate_daily_engagement,
        trigger=CronTrigger(hour=1, minute=0),
        id="aggregate_daily_engagement",
        name="Aggregate Daily Engagement",
        replace_existing=True,
        max_instances=1,
        coalesce=True
    )
    logger.info("✓ Scheduled: aggregate_daily_engagement (daily at 1:00 AM)")

    # Task 3: Generate weekly report every Monday at 9:00 AM UTC
    _scheduler.add_job(
        generate_weekly_kpi_report,
        trigger=CronTrigger(day_of_week='mon', hour=9, minute=0),
        id="generate_weekly_kpi_report",
        name="Generate Weekly KPI Report",
        replace_existing=True,
        max_instances=1,
        coalesce=True
    )
    logger.info("✓ Scheduled: generate_weekly_kpi_report (Monday at 9:00 AM)")

    # Task 4: Cleanup old metrics every Sunday at 3:00 AM UTC
    _scheduler.add_job(
        cleanup_old_metrics,
        trigger=CronTrigger(day_of_week='sun', hour=3, minute=0),
        id="cleanup_old_metrics",
        name="Cleanup Old Metrics",
        replace_existing=True,
        max_instances=1,
        coalesce=True
    )
    logger.info("✓ Scheduled: cleanup_old_metrics (Sunday at 3:00 AM)")

    # Task 5: Cleanup orphaned KPI embeddings daily at 2:00 AM UTC
    _scheduler.add_job(
        cleanup_orphaned_kpi_embeddings,
        trigger=CronTrigger(hour=2, minute=0),
        id="cleanup_orphaned_kpi_embeddings",
        name="Cleanup Orphaned KPI Embeddings",
        replace_existing=True,
        max_instances=1,
        coalesce=True
    )
    logger.info("Scheduled: cleanup_orphaned_kpi_embeddings (daily at 2:00 AM)")

    # Start scheduler
    _scheduler.start()
    logger.info("=" * 60)
    logger.info("KPI Scheduler started successfully")
    logger.info("All tasks registered and running")
    logger.info("=" * 60)


def get_scheduler_status() -> Dict[str, Any]:
    """
    Returns current scheduler status and job information.
    Used by health check endpoint.
    """
    if _scheduler is None:
        return {"status": "not_running", "jobs": []}

    jobs = []
    for job in _scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })

    return {
        "status": "running" if _scheduler.running else "stopped",
        "jobs": jobs,
        "job_count": len(jobs)
    }


async def stop_scheduler():
    """
    Gracefully stops the scheduler.
    Called during application shutdown.
    """
    global _scheduler

    if _scheduler is None:
        return

    logger.info("Stopping KPI Scheduler...")
    _scheduler.shutdown(wait=True)
    _scheduler = None
    logger.info("KPI Scheduler stopped")


# ============================================================================
# Manual Trigger Functions (for testing/debugging)
# ============================================================================

async def trigger_refresh_views():
    """Manual trigger for view refresh (for testing)"""
    return await refresh_materialized_views()


async def trigger_daily_engagement():
    """Manual trigger for daily engagement aggregation (for testing)"""
    return await aggregate_daily_engagement()


async def trigger_weekly_report():
    """Manual trigger for weekly report generation (for testing)"""
    return await generate_weekly_kpi_report()


async def trigger_cleanup():
    """Manual trigger for metric cleanup (for testing)"""
    return await cleanup_old_metrics()


async def trigger_kpi_embedding_cleanup():
    """Manual trigger for KPI embedding cleanup (for testing)"""
    return await cleanup_orphaned_kpi_embeddings()
