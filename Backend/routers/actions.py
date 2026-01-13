from fastapi import APIRouter, HTTPException, status
from core.database import get_db, get_db_context
from core.models import ActionCreate

router = APIRouter(prefix="/api/actions", tags=["Actions"])

@router.post("", status_code=status.HTTP_201_CREATED)
def create_action(action: ActionCreate):
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO actions (user_id, recommendation_id, action_taken, result)
            VALUES (%s, %s, %s, %s)
            RETURNING *
        """, (action.user_id, action.recommendation_id, action.action_taken, action.result))
        result = cursor.fetchone()
        if action.recommendation_id:
            cursor.execute("""
                UPDATE recommendations SET status = 'acted'
                WHERE id = %s AND status = 'pending'
            """, (action.recommendation_id,))
        conn.commit()
        return {"success": True, "data": result}

@router.get("/user/{user_id}")
def get_user_actions(user_id: int):
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, r.title as recommendation_title, r.confidence
            FROM actions a
            LEFT JOIN recommendations r ON r.id = a.recommendation_id
            WHERE a.user_id = %s
            ORDER BY a.taken_at DESC
        """, (user_id,))
        return {"success": True, "data": cursor.fetchall()}
