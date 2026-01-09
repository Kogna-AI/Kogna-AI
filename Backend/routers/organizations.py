from fastapi import APIRouter, HTTPException, status, Depends
from core.database import get_db
from core.models import OrganizationCreate
from core.permissions import require_permission, UserContext

router = APIRouter(prefix="/api/organizations", tags=["Organizations"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_organization(
    org: OrganizationCreate,
    user_ctx: UserContext = Depends(
        require_permission("organizations", "create", "org"),
    ),
):
    """Create an organization.

    RBAC v1:
    - Protected by explicit permission organizations:create:org
    - Default-deny for callers without this permission.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO organizations (name, industry, team_due, team, project_number)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
            """,
            (org.name, org.industry, org.team_due, org.team, org.project_number),
        )
        result = cursor.fetchone()
        return {"success": True, "data": result}


@router.get("/me")
async def get_my_organization(
    user_ctx: UserContext = Depends(
        require_permission("organizations", "read", "self"),
    ),
):
    """Return the caller's own organization record.

    Enforces org_id = user_ctx.organization_id at the SQL layer as the final
    boundary.
    """
    if not user_ctx.organization_id:
        raise HTTPException(status_code=404, detail="Organization not found")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM organizations WHERE id = %s",
            (user_ctx.organization_id,),
        )
        data = cursor.fetchone()
        if not data:
            # Do not leak whether other orgs exist; 404 is safe for caller's org
            raise HTTPException(status_code=404, detail="Organization not found")
        return {"success": True, "data": data}
