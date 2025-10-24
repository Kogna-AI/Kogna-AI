from fastapi import APIRouter, HTTPException, status
from core.database import get_db
from core.models import RecommendationCreate, RecommendationReasonCreate
from psycopg2.extras import Json

router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])

@router.post("", status_code=status.HTTP_201_CREATED)
def create_recommendation(rec: RecommendationCreate):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO recommendations (organization_id, title, recommendation, confidence, action, created_for)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *
        """, (rec.organization_id, rec.title, rec.recommendation,
              rec.confidence, rec.action, rec.created_for))
        result = cursor.fetchone()
        conn.commit()
        return {"success": True, "data": result}

@router.get("/{rec_id}")
def get_recommendation(rec_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM recommendations WHERE id = %s", (rec_id,))
        rec = cursor.fetchone()
        if not rec:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        return {"success": True, "data": rec}

@router.post("/{rec_id}/reasons", status_code=status.HTTP_201_CREATED)
def add_reason(rec_id: int, reason: RecommendationReasonCreate):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO recommendation_reasons (recommendation_id, reason, evidence_datasets_id)
            VALUES (%s, %s, %s)
            RETURNING *
        """, (rec_id, reason.reason, Json(reason.evidence_datasets_id) if reason.evidence_datasets_id else None))
        result = cursor.fetchone()
        conn.commit()
        return {"success": True, "data": result}
