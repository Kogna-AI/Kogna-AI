from fastapi import APIRouter, status
from core.database import get_db
from core.models import FeedbackCreate

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])

@router.post("", status_code=status.HTTP_201_CREATED)
def create_feedback(feedback: FeedbackCreate):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO feedback (user_id, rating, comments)
            VALUES (%s, %s, %s)
            RETURNING *
        """, (feedback.user_id, feedback.rating, feedback.comments))
        result = cursor.fetchone()
        conn.commit()
        return {"success": True, "data": result}
