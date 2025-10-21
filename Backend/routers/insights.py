from fastapi import APIRouter, HTTPException, status
from core.database import get_db
from core.models import AIInsightCreate

router = APIRouter(prefix="/api/insights", tags=["AI Insights"])

@router.post("", status_code=status.HTTP_201_CREATED)
def create_insight(insight: AIInsightCreate):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ai_insights (organization_id, category, title, description, confidence, level)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *
        """, (insight.organization_id, insight.category, insight.title,
              insight.description, insight.confidence, insight.level))
        result = cursor.fetchone()
        conn.commit()
        return {"success": True, "data": result}

@router.get("/org/{org_id}")
def list_insights(org_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM ai_insights
            WHERE organization_id = %s AND status = 'active'
            ORDER BY confidence DESC
            LIMIT 50
        """, (org_id,))
        return {"success": True, "data": cursor.fetchall()}
