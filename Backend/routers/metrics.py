from fastapi import APIRouter, HTTPException, status
from core.database import get_db, get_db_context
from core.models import MetricCreate

router = APIRouter(prefix="/api/metrics", tags=["Metrics"])

@router.post("", status_code=status.HTTP_201_CREATED)
def create_metric(metric: MetricCreate):
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO metrics (organization_id, name, value, unit, change_from_last)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
        """, (metric.organization_id, metric.name, metric.value, metric.unit, metric.change_from_last))
        result = cursor.fetchone()
        conn.commit()
        return {"success": True, "data": result}

@router.get("/{metric_id}")
def get_metric(metric_id: int):
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM metrics WHERE id = %s", (metric_id,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Metric not found")
        return {"success": True, "data": result}

@router.get("/org/{org_id}")
def list_metrics(org_id: int):
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM metrics 
            WHERE organization_id = %s
            ORDER BY last_updated DESC
        """, (org_id,))
        return {"success": True, "data": cursor.fetchall()}
