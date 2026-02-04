import os
from dotenv import load_dotenv

# 1. FORCE LOAD ENV VARIABLES
load_dotenv() 

from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from pydantic import BaseModel
from services.bi_system_service import BISystemService

router = APIRouter(
    prefix="/api/bi-systems",
    tags=["bi-systems"]
)

# 2. SAFE INITIALIZATION
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

if not supabase_url or not supabase_key:
    print("CRITICAL WARNING: SUPABASE_URL or SUPABASE_SERVICE_KEY is missing in .env")

service = BISystemService(
    supabase_url=supabase_url if supabase_url else "",
    supabase_key=supabase_key if supabase_key else ""
)

# ==================================================================
# 1. SPECIFIC ROUTES (MUST BE FIRST!)
# ==================================================================

@router.get("/available")
async def get_available_bi_tools():
    """Return list of supported BI tools"""
    return service.get_available_bi_tools()

# ==================================================================
# 2. GENERAL ROUTES
# ==================================================================

class AddBISystemRequest(BaseModel):
    bi_tool: str
    report_id: Optional[str] = None
    workspace_id: Optional[str] = None
    embed_code: Optional[str] = None
    custom_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

@router.get("/")
async def get_user_bi_systems(x_user_id: str = Header(None)):
    """Get all BI systems for the current user"""
    if not x_user_id:
        raise HTTPException(status_code=400, detail="X-User-ID header required")
    try:
        return service.get_user_bi_systems(x_user_id)
    except Exception as e:
        print(f"Error getting systems: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/")
async def add_bi_system(request: AddBISystemRequest, x_user_id: str = Header(None)):
    """Add a new BI system configuration"""
    if not x_user_id:
        raise HTTPException(status_code=400, detail="X-User-ID header required")
    
    try:
        # Fetch organization_id from user
        user_data = service.supabase.table('users').select('organization_id').eq('id', x_user_id).single().execute()
        
        if not user_data.data:
            raise HTTPException(status_code=404, detail="User not found")
            
        organization_id = user_data.data['organization_id']
        
        return service.add_bi_system(
            organization_id=organization_id,
            bi_tool=request.bi_tool,
            report_id=request.report_id,
            workspace_id=request.workspace_id,
            embed_code=request.embed_code,
            custom_url=request.custom_url,
            thumbnail_url=request.thumbnail_url
        )
    except Exception as e:
        print(f"Error adding BI system: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ==================================================================
# 3. DYNAMIC ROUTES (MUST BE LAST!)
# ==================================================================

@router.get("/{bi_system_id}/url")
async def get_bi_system_url(bi_system_id: str, x_user_id: str = Header(None)):
    """Get the secure embed URL/Token for a specific system"""
    if not x_user_id:
        raise HTTPException(status_code=400, detail="X-User-ID header required")
    try:
        # CRITICAL: We pass x_user_id to the service so it can fetch the USER'S specific OAuth token
        return await service.get_bi_system_url(bi_system_id, x_user_id)
    except Exception as e:
        print(f"Error fetching URL: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/powerbi/reports")
async def get_powerbi_reports(x_user_id: str = Header(None)):
    """Fetch list of available Power BI reports for the dropdown"""
    if not x_user_id:
        raise HTTPException(status_code=400, detail="X-User-ID header required")
    try:
        return await service.get_user_powerbi_reports(x_user_id)
    except Exception as e:
        print(f"Error fetching PBI reports: {e}")
        # Return empty list instead of crashing, so frontend can show "No reports found"
        return []

@router.delete("/{bi_tool}")
async def delete_bi_system(bi_tool: str, x_user_id: str = Header(None)):
    """Remove a BI system"""
    if not x_user_id:
        raise HTTPException(status_code=400, detail="X-User-ID header required")

    try:
        user_data = service.supabase.table('users').select('organization_id').eq('id', x_user_id).single().execute()
        organization_id = user_data.data['organization_id']

        service.supabase.table('customer_bi_systems')\
            .delete()\
            .eq('organization_id', organization_id)\
            .eq('bi_tool', bi_tool)\
            .execute()

        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/google-drive/files")
async def get_google_drive_files(x_user_id: str = Header(None)):
    """Get Google Drive files used for data analysis"""
    if not x_user_id:
        raise HTTPException(status_code=400, detail="X-User-ID header required")

    try:
        # Fetch files from ingested_files table where source_type is 'google_drive'
        response = service.supabase.table('ingested_files')\
            .select('id, file_name, file_path, file_size, source_id, source_metadata, last_ingested_at, chunk_count')\
            .eq('user_id', x_user_id)\
            .eq('source_type', 'google_drive')\
            .order('last_ingested_at', desc=True)\
            .limit(10)\
            .execute()

        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching Google Drive files: {e}")
        return []