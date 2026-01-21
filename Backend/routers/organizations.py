from fastapi import APIRouter, HTTPException, status,Depends
from core.database import get_db, get_db_context
from core.models import OrganizationCreate
from auth.dependencies import get_current_user

router = APIRouter(prefix="/api/organizations", tags=["Organizations"])

@router.post("", status_code=status.HTTP_201_CREATED)
def create_organization(org: OrganizationCreate):  
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO organizations (name, industry, team_due, team, project_number)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
        """, (org.name, org.industry, org.team_due, org.team, org.project_number))
        result = cursor.fetchone()
        conn.commit()
        return {"success": True, "data": result}

@router.get("/{org_id}")
def get_organization(org_id: int, user=Depends(get_current_user)): 
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM organizations WHERE id = %s", (org_id,))
        data = cursor.fetchone()
        if not data:
            raise HTTPException(status_code=404, detail="Organization not found")
        return {"success": True, "data": data}
