from fastapi import APIRouter, HTTPException, status
from core.database import get_db
from core.models import ObjectiveCreate, ObjectiveUpdate, GrowthStageCreate, MilestoneCreate
from datetime import datetime

router = APIRouter(prefix="/api/objectives", tags=["Objectives"])

@router.post("", status_code=status.HTTP_201_CREATED)
def create_objective(obj: ObjectiveCreate):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO objectives (organization_id, title, progress, status, team_responsible)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
        """, (obj.organization_id, obj.title, obj.progress, obj.status, obj.team_responsible))
        result = cursor.fetchone()
        conn.commit()
        return {"success": True, "data": result}

@router.put("/{obj_id}")
def update_objective(obj_id: int, obj: ObjectiveUpdate):
    with get_db() as conn:
        cursor = conn.cursor()
        updates = []
        params = []

        if obj.title: updates.append("title = %s"); params.append(obj.title)
        if obj.progress is not None:
            updates.append("progress = %s"); params.append(obj.progress)
            if obj.progress >= 80: updates.append("status = 'ahead'")
            elif obj.progress >= 50: updates.append("status = 'on-track'")
            else: updates.append("status = 'at-risk'")
        if obj.status: updates.append("status = %s"); params.append(obj.status)
        if obj.team_responsible: updates.append("team_responsible = %s"); params.append(obj.team_responsible)
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        params.append(obj_id)
        query = f"UPDATE objectives SET {', '.join(updates)} WHERE id = %s RETURNING *"
        cursor.execute(query, params)
        result = cursor.fetchone()
        conn.commit()
        if not result:
            raise HTTPException(status_code=404, detail="Objective not found")
        return {"success": True, "data": result}
