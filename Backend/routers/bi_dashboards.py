"""
BI Dashboard Embedding - API Router
Endpoints for managing BI tool connections, dashboard registry, and embed token generation.
"""
import json
import logging
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, status, Depends, Query
from psycopg2.extras import RealDictCursor, Json

from core.database import get_db
from core.bi_models import (
    BIProvider, BIConnectorCreate, BIConnectorUpdate,
    BIConnectorResponse, BIDashboardRegister, BIDashboardResponse,
    EmbedTokenResponse, ExecDashboardResponse, ExecKPISummaryCard,
)
from auth.dependencies import get_backend_user_id
from services.bi_embed_service import BIEmbedService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bi", tags=["BI Dashboards"])


# ============================================================================
# BI Connector CRUD
# ============================================================================

@router.get("/connectors")
def list_bi_connectors(
    user=Depends(get_backend_user_id),
    db=Depends(get_db),
):
    """List all BI connectors for the user's organization."""
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        SELECT bc.*,
               (SELECT COUNT(*) FROM bi_dashboards bd
                WHERE bd.bi_connector_id = bc.id) AS dashboard_count
        FROM bi_connectors bc
        WHERE bc.organization_id = %s
        ORDER BY bc.created_at DESC
        """,
        (user["organization_id"],),
    )
    rows = cursor.fetchall()
    return {"success": True, "data": rows}


@router.post("/connectors", status_code=status.HTTP_201_CREATED)
def create_bi_connector(
    data: BIConnectorCreate,
    user=Depends(get_backend_user_id),
    db=Depends(get_db),
):
    """Create a new BI tool connection."""
    cursor = db.cursor(cursor_factory=RealDictCursor)

    cursor.execute(
        """
        INSERT INTO bi_connectors
            (user_id, organization_id, team_id, provider, display_name,
             server_url, site_name, api_key, api_secret, embed_secret,
             tenant_id, workspace_id, config, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'configured')
        ON CONFLICT (user_id, organization_id, provider)
        DO UPDATE SET
            display_name = EXCLUDED.display_name,
            server_url = EXCLUDED.server_url,
            site_name = EXCLUDED.site_name,
            api_key = EXCLUDED.api_key,
            api_secret = EXCLUDED.api_secret,
            embed_secret = EXCLUDED.embed_secret,
            tenant_id = EXCLUDED.tenant_id,
            workspace_id = EXCLUDED.workspace_id,
            config = EXCLUDED.config,
            status = 'configured'
        RETURNING *
        """,
        (
            user["user_id"], user["organization_id"], user.get("team_id"),
            data.provider.value, data.display_name or data.provider.value.title(),
            data.server_url, data.site_name,
            data.api_key, data.api_secret, data.embed_secret,
            data.tenant_id, data.workspace_id, Json(data.config),
        ),
    )
    row = cursor.fetchone()
    db.commit()
    return {"success": True, "message": f"{data.provider.value} connector created", "data": row}


@router.put("/connectors/{connector_id}")
def update_bi_connector(
    connector_id: str,
    data: BIConnectorUpdate,
    user=Depends(get_backend_user_id),
    db=Depends(get_db),
):
    """Update BI connector configuration."""
    cursor = db.cursor(cursor_factory=RealDictCursor)

    # Build dynamic SET clause from non-None fields
    updates = {}
    for field_name, value in data.model_dump(exclude_none=True).items():
        updates[field_name] = value

    if not updates:
        raise HTTPException(400, "No fields to update")

    set_parts = []
    values = []
    for key, val in updates.items():
        if key == "config":
            set_parts.append(f"{key} = %s")
            values.append(Json(val))
        else:
            set_parts.append(f"{key} = %s")
            values.append(val)

    set_parts.append("status = 'configured'")
    values.extend([connector_id, user["organization_id"]])

    cursor.execute(
        f"""
        UPDATE bi_connectors SET {', '.join(set_parts)}
        WHERE id = %s AND organization_id = %s
        RETURNING *
        """,
        values,
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(404, "Connector not found")
    db.commit()
    return {"success": True, "data": row}


@router.delete("/connectors/{connector_id}")
def delete_bi_connector(
    connector_id: str,
    user=Depends(get_backend_user_id),
    db=Depends(get_db),
):
    """Delete a BI connector and its dashboards (CASCADE)."""
    cursor = db.cursor()
    cursor.execute(
        "DELETE FROM bi_connectors WHERE id = %s AND organization_id = %s",
        (connector_id, user["organization_id"]),
    )
    if cursor.rowcount == 0:
        raise HTTPException(404, "Connector not found")
    db.commit()
    return {"success": True, "message": "Connector deleted"}


@router.post("/connectors/{connector_id}/test")
async def test_bi_connection(
    connector_id: str,
    user=Depends(get_backend_user_id),
    db=Depends(get_db),
):
    """Test a BI connector's connectivity and update status."""
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        "SELECT * FROM bi_connectors WHERE id = %s AND organization_id = %s",
        (connector_id, user["organization_id"]),
    )
    connector = cursor.fetchone()
    if not connector:
        raise HTTPException(404, "Connector not found")

    try:
        # Attempt a simple embed generation to validate credentials
        dummy_dashboard = {"external_dashboard_id": "test", "embed_config": {}}
        await BIEmbedService.generate_embed(
            connector["provider"], dict(connector), dummy_dashboard
        )
        new_status = "connected"
        error_msg = None
    except Exception as e:
        new_status = "error"
        error_msg = str(e)
        logger.warning(f"BI connection test failed for {connector_id}: {e}")

    cursor.execute(
        """
        UPDATE bi_connectors
        SET status = %s, last_verified_at = NOW(), error_message = %s
        WHERE id = %s
        """,
        (new_status, error_msg, connector_id),
    )
    db.commit()
    return {
        "success": new_status == "connected",
        "status": new_status,
        "error_message": error_msg,
    }


@router.get("/connectors/status")
def get_bi_connection_status(
    user=Depends(get_backend_user_id),
    db=Depends(get_db),
):
    """Get connection status for all BI providers (mirrors /api/connect/status)."""
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        SELECT provider, status, last_verified_at, display_name, error_message,
               (SELECT COUNT(*) FROM bi_dashboards bd
                WHERE bd.bi_connector_id = bc.id) AS dashboard_count
        FROM bi_connectors bc
        WHERE bc.organization_id = %s
        """,
        (user["organization_id"],),
    )
    rows = cursor.fetchall()
    connections = {}
    for row in rows:
        connections[row["provider"]] = {
            "status": row["status"],
            "last_verified_at": str(row["last_verified_at"]) if row["last_verified_at"] else None,
            "display_name": row["display_name"],
            "dashboard_count": row["dashboard_count"],
            "error_message": row["error_message"],
        }
    return {"success": True, "connections": connections}


# ============================================================================
# Dashboard Registry
# ============================================================================

@router.get("/dashboards")
def list_bi_dashboards(
    connector_id: Optional[str] = Query(None),
    user=Depends(get_backend_user_id),
    db=Depends(get_db),
):
    """List registered dashboards, optionally filtered by connector."""
    cursor = db.cursor(cursor_factory=RealDictCursor)

    if connector_id:
        cursor.execute(
            """
            SELECT bd.*, bc.provider
            FROM bi_dashboards bd
            JOIN bi_connectors bc ON bd.bi_connector_id = bc.id
            WHERE bd.organization_id = %s AND bd.bi_connector_id = %s
            ORDER BY bd.sort_order, bd.created_at
            """,
            (user["organization_id"], connector_id),
        )
    else:
        cursor.execute(
            """
            SELECT bd.*, bc.provider
            FROM bi_dashboards bd
            JOIN bi_connectors bc ON bd.bi_connector_id = bc.id
            WHERE bd.organization_id = %s
            ORDER BY bd.sort_order, bd.created_at
            """,
            (user["organization_id"],),
        )

    rows = cursor.fetchall()
    return {"success": True, "data": rows}


@router.post("/dashboards", status_code=status.HTTP_201_CREATED)
def register_bi_dashboard(
    data: BIDashboardRegister,
    user=Depends(get_backend_user_id),
    db=Depends(get_db),
):
    """Register a dashboard for embedding."""
    cursor = db.cursor(cursor_factory=RealDictCursor)

    # Verify connector belongs to org
    cursor.execute(
        "SELECT id FROM bi_connectors WHERE id = %s AND organization_id = %s",
        (data.bi_connector_id, user["organization_id"]),
    )
    if not cursor.fetchone():
        raise HTTPException(404, "BI connector not found")

    cursor.execute(
        """
        INSERT INTO bi_dashboards
            (bi_connector_id, organization_id, external_dashboard_id,
             name, description, embed_url, embed_config, is_default, is_public)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *
        """,
        (
            data.bi_connector_id, user["organization_id"],
            data.external_dashboard_id, data.name, data.description,
            data.embed_url, Json(data.embed_config),
            data.is_default, data.is_public,
        ),
    )
    row = cursor.fetchone()
    db.commit()
    return {"success": True, "data": row}


@router.delete("/dashboards/{dashboard_id}")
def remove_bi_dashboard(
    dashboard_id: str,
    user=Depends(get_backend_user_id),
    db=Depends(get_db),
):
    """Remove a registered dashboard."""
    cursor = db.cursor()
    cursor.execute(
        "DELETE FROM bi_dashboards WHERE id = %s AND organization_id = %s",
        (dashboard_id, user["organization_id"]),
    )
    if cursor.rowcount == 0:
        raise HTTPException(404, "Dashboard not found")
    db.commit()
    return {"success": True, "message": "Dashboard removed"}


# ============================================================================
# Embed Token Generation
# ============================================================================

@router.get("/dashboards/{dashboard_id}/embed")
async def get_embed_token(
    dashboard_id: str,
    user=Depends(get_backend_user_id),
    db=Depends(get_db),
):
    """Generate a secure embed token/URL for the specified dashboard."""
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        SELECT bd.*, bc.provider, bc.server_url, bc.site_name,
               bc.api_key, bc.api_secret, bc.embed_secret,
               bc.tenant_id, bc.workspace_id, bc.config AS connector_config
        FROM bi_dashboards bd
        JOIN bi_connectors bc ON bd.bi_connector_id = bc.id
        WHERE bd.id = %s AND bd.organization_id = %s
        """,
        (dashboard_id, user["organization_id"]),
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(404, "Dashboard not found")

    connector_config = {
        "server_url": row["server_url"],
        "site_name": row["site_name"],
        "api_key": row["api_key"],
        "api_secret": row["api_secret"],
        "embed_secret": row["embed_secret"],
        "tenant_id": row["tenant_id"],
        "workspace_id": row["workspace_id"],
        "config": row["connector_config"] if isinstance(row["connector_config"], dict) else {},
    }
    dashboard_config = {
        "external_dashboard_id": row["external_dashboard_id"],
        "embed_url": row["embed_url"],
        "embed_config": row["embed_config"] if isinstance(row["embed_config"], dict) else {},
    }

    try:
        result = await BIEmbedService.generate_embed(
            row["provider"], connector_config, dashboard_config
        )
        result["dashboard_id"] = dashboard_id

        # Update last_accessed_at
        cursor.execute(
            "UPDATE bi_dashboards SET last_accessed_at = NOW() WHERE id = %s",
            (dashboard_id,),
        )
        db.commit()

        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Embed generation failed: {e}")
        raise HTTPException(500, f"Failed to generate embed: {str(e)}")


# ============================================================================
# Executive Dashboard (Native KPI View)
# ============================================================================

@router.get("/executive-dashboard")
def get_executive_dashboard(
    period: str = Query(default="ytd", pattern="^(ytd|monthly|quarterly)$"),
    user=Depends(get_backend_user_id),
    db=Depends(get_db),
):
    """
    Returns KPI summary data for the native executive dashboard.
    Falls back to demo data if no snapshots exist.
    """
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        SELECT category, kpi_name, kpi_value, kpi_unit,
               previous_value, change_percent, trend_direction,
               period_label, breakdown, monthly_trend
        FROM executive_kpi_snapshots
        WHERE organization_id = %s AND period_type = %s
        ORDER BY snapshot_date DESC
        """,
        (user["organization_id"], period),
    )
    rows = cursor.fetchall()

    if not rows:
        # Return null so frontend uses mock data
        return {"success": True, "data": None}

    # Group by category
    grouped = {}
    for row in rows:
        cat = row["category"]
        if cat not in grouped:
            grouped[cat] = row

    return {"success": True, "data": grouped, "period": period}
