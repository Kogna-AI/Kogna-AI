from fastapi import APIRouter, HTTPException, status, Depends
from core.database import get_db
from core.models import UserCreate
import psycopg2

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate):
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (organization_id, first_name, second_name, role, email)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *
            """, (user.organization_id, user.first_name, user.second_name, user.role, user.email))
            result = cursor.fetchone()
            conn.commit()
            return {"success": True, "data": result}
        except psycopg2.IntegrityError:
            raise HTTPException(status_code=400, detail="Email already exists")

@router.get("/{user_id}")
def get_user(user_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
        return {"success": True, "data": result}


@router.get("/by-supabase/{supabase_id}")
def get_user_by_supabase_id(supabase_id: str, db=Depends(get_db)):
    # db here is the connection object
    cursor = db.cursor()  # ✅ create a cursor from the connection

    cursor.execute("SELECT * FROM users WHERE supabase_id = %s", (supabase_id,))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        raise HTTPException(status_code=404, detail="User not found")

    cursor.close()
    return {"success": True, "data": user}