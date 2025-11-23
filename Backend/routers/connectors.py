# Add this to your routers/connectors.py (COMPLETE VERSION WITH ALL ENDPOINTS)

import os
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from urllib.parse import quote
import httpx
import logging
import time
from services.etl_pipelines import run_master_etl, run_test
from routers.Authentication import get_backend_user_id
from supabase_connect import get_supabase_manager
from typing import List, Optional
from pydantic import BaseModel

supabase = get_supabase_manager().client

# --- Environment Variables ---
JIRA_CLIENT_ID = os.getenv("JIRA_CLIENT_ID")
JIRA_CLIENT_SECRET = os.getenv("JIRA_CLIENT_SECRET")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
ASANA_CLIENT_ID = os.getenv("ASANA_CLIENT_ID")
ASANA_CLIENT_SECRET = os.getenv("ASANA_CLIENT_SECRET")

APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")

# --- Pydantic Models ---
class SyncJobOut(BaseModel):
    id: str
    service: str
    status: str
    progress: Optional[str]
    files_processed: int
    started_at: int
    finished_at: Optional[int]
    error_message: Optional[str]
    duration_seconds: Optional[int]

# --- Routers ---
connect_router = APIRouter(prefix="/api/connect", tags=["Connectors"])
callback_router = APIRouter(tags=["Connectors"])

# =================================================================
# SYNC STATUS ENDPOINTS (NEW)
# =================================================================

@connect_router.get("/sync-status", response_model=List[SyncJobOut])
async def get_sync_status(ids: dict = Depends(get_backend_user_id)):
    """
    Get all sync jobs for the authenticated user.
    Shows current progress, completed jobs, and any errors.
    """
    user_id = ids.get('user_id')
    
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    try:
        response = supabase.table("sync_jobs") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .limit(50) \
            .execute()
        
        jobs = response.data or []
        
        # Calculate duration for each job
        for job in jobs:
            if job.get('finished_at'):
                duration = job['finished_at'] - job['started_at']
                job['duration_seconds'] = duration
            else:
                # Job still running
                duration = int(time.time()) - job['started_at']
                job['duration_seconds'] = duration
        
        return jobs
    
    except Exception as e:
        logging.error(f"Error fetching sync status: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch sync status")

@connect_router.get("/sync-status/{service}", response_model=Optional[SyncJobOut])
async def get_sync_status_for_service(
    service: str, 
    ids: dict = Depends(get_backend_user_id)
):
    """
    Get the most recent sync job status for a specific service.
    Useful for showing "Syncing..." indicators in the UI.
    """
    user_id = ids.get('user_id')
    
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    try:
        response = supabase.table("sync_jobs") \
            .select("*") \
            .eq("user_id", user_id) \
            .eq("service", service) \
            .order("created_at", desc=True) \
            .limit(1) \
            .maybe_single() \
            .execute()
        
        job = response.data
        
        if job:
            if job.get('finished_at'):
                duration = job['finished_at'] - job['started_at']
            else:
                duration = int(time.time()) - job['started_at']
            
            job['duration_seconds'] = duration
            return job
        
        return None
    
    except Exception as e:
        logging.error(f"Error fetching sync status for {service}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch sync status")

@connect_router.delete("/sync-status/{job_id}")
async def clear_sync_job(
    job_id: str,
    ids: dict = Depends(get_backend_user_id)
):
    """
    Clear/delete a sync job record.
    Only completed or failed jobs can be cleared.
    """
    user_id = ids.get('user_id')
    
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    try:
        response = supabase.table("sync_jobs") \
            .select("*") \
            .eq("id", job_id) \
            .eq("user_id", user_id) \
            .maybe_single() \
            .execute()
        
        job = response.data
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job['status'] == 'running':
            raise HTTPException(status_code=400, detail="Cannot clear running job")
        
        supabase.table("sync_jobs") \
            .delete() \
            .eq("id", job_id) \
            .execute()
        
        return {"status": "deleted", "job_id": job_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error clearing sync job: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear sync job")

# =================================================================
# EXISTING ENDPOINTS (UNCHANGED)
# =================================================================

@connect_router.get("/test")
async def run_simple_test():
    """Runs the simple httpx test."""
    return await run_test()

@connect_router.get("/{provider}")
async def connect_to_service(provider: str, ids: dict = Depends(get_backend_user_id)):
    """Initiates OAuth flow for a given provider."""
    user_id = ids.get('user_id')
    if not user_id:
        logging.error("Connect attempted without valid user ID.")
        return {"error": "Authentication failed: User ID not found."}

    state = f"oauth_{user_id}"

    if provider == "jira":
        scopes = ["read:jira-work", "read:jira-user", "offline_access"]
        scope = quote(" ".join(scopes))
        redirect_uri = f"{APP_BASE_URL}/auth/callback/jira"
        
        auth_url = (
            f"https://auth.atlassian.com/authorize?"
            f"audience=api.atlassian.com&"
            f"client_id={JIRA_CLIENT_ID}&"
            f"scope={scope}&"
            f"redirect_uri={redirect_uri}&"
            f"state={state}&"
            f"response_type=code&"
            f"prompt=consent"
        )
        return JSONResponse({"url": auth_url})

    if provider == "google":
        scopes = [
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/userinfo.email",
            "openid"
        ]
        scope = quote(" ".join(scopes))
        redirect_uri = f"{APP_BASE_URL}/auth/callback/google"
        logging.info(f"Google redirect_uri being used: {redirect_uri}")

        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={GOOGLE_CLIENT_ID}&"
            f"redirect_uri={redirect_uri}&"
            f"response_type=code&"
            f"scope={scope}&"
            f"access_type=offline&"
            f"prompt=consent&"
            f"state={state}"
        )
        logging.info(f"=== GOOGLE AUTH DEBUG ===")
        logging.info(f"Client ID: {GOOGLE_CLIENT_ID}")
        logging.info(f"Redirect URI: {redirect_uri}")
        logging.info(f"Full Auth URL: {auth_url}")
        logging.info(f"========================")
        return JSONResponse({"url": auth_url})

    if provider == "microsoft-excel":
        scopes = [
            "Files.Read.All",
            "Files.ReadWrite.All",
            "User.Read",
            "offline_access",
            "Files.Read",
            "Files.ReadWrite",
            "Sites.Read.All"
        ]
        scope = quote(" ".join(scopes))
        state = f"auth_{user_id}_excel_{int(time.time())}"
        redirect_uri = f"{APP_BASE_URL}/auth/callback/microsoft"

        auth_url = (
            "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
            f"client_id={MICROSOFT_CLIENT_ID}&"
            f"response_type=code&"
            f"redirect_uri={redirect_uri}&"
            f"scope={scope}&"
            f"response_mode=query&"
            f"state={state}&"
            f"prompt=consent"
        )
        return JSONResponse({"url": auth_url})

    if provider == "microsoft-project":
        scopes = [
           "User.Read",
            "offline_access",
            "Group.Read.All",
            "Tasks.Read",
            "Sites.Read.All"
        ]
        scope = quote(" ".join(scopes))
        state = f"auth_{user_id}_project_{int(time.time())}"
        redirect_uri = f"{APP_BASE_URL}/auth/callback/microsoft"

        auth_url = (
            f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
            f"client_id={MICROSOFT_CLIENT_ID}&"
            f"response_type=code&"
            f"redirect_uri={redirect_uri}&"
            f"scope={scope}&"
            f"response_mode=query&"
            f"state={state}&"
            f"prompt=consent"
        )
        return JSONResponse({"url": auth_url})
    
    if provider == "microsoft-teams":
        scopes = [
            "Team.ReadBasic.All",
            "Group.Read.All",
            "Channel.ReadBasic.All",
            "ChannelMessage.Read.All",
            "User.Read",
            "offline_access"
        ]
        scope = quote(" ".join(scopes))
        state = f"auth_{user_id}_teams_{int(time.time())}"
        redirect_uri = f"{APP_BASE_URL}/auth/callback/microsoft"

        auth_url = (
            "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
            f"client_id={MICROSOFT_CLIENT_ID}&"
            f"response_type=code&"
            f"redirect_uri={quote(redirect_uri)}&"
            f"scope={scope}&"
            f"response_mode=query&"
            f"state={state}&"
            f"prompt=consent"
        )
        return JSONResponse({"url": auth_url})

    if provider == "asana":
        scopes = [
        "tasks:read",
        "projects:read",
        "users:read",
        "workspaces:read",
    ]
        scope = quote(" ".join(scopes))
        state = f"oauth_{user_id}_asana_{int(time.time())}"
        redirect_uri = f"{APP_BASE_URL}/auth/callback/asana"

        auth_url = (
            "https://app.asana.com/-/oauth_authorize?"
            f"client_id={ASANA_CLIENT_ID}&"
            f"redirect_uri={quote(redirect_uri)}&"
            f"response_type=code&"
            f"state={state}&"
            f"scope={scope}&"
            f"prompt=consent"
        )
        return JSONResponse({"url": auth_url})

    return {"error": "Unknown provider"}

@callback_router.get("/auth/callback/{provider}")
async def auth_callback(
    provider: str,
    code: str,
    state: str,
    background_tasks: BackgroundTasks,
):
    """
    Handles callback from any provider - SAVES TOKENS + TRIGGERS ETL
    Then redirects user back to frontend homepage
    """
    try:
        user_id = state.split('_')[1]
    except IndexError:
        logging.error(f"Invalid state format received: {state}")
        return RedirectResponse(url="http://localhost:3000")

    async with httpx.AsyncClient() as client:
        try:
            if provider == "jira":
                token_url = "https://auth.atlassian.com/oauth/token"
                redirect_uri = f"{APP_BASE_URL}/auth/callback/jira"
                payload = {
                    "grant_type": "authorization_code",
                    "client_id": JIRA_CLIENT_ID,
                    "client_secret": JIRA_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": redirect_uri,
                }

                response = await client.post(token_url, json=payload)
                response.raise_for_status()
                token_data = response.json()

                access_token = token_data.get("access_token")
                refresh_token = token_data.get("refresh_token")
                expires_in = token_data.get("expires_in", 3600)

                resources_url = "https://api.atlassian.com/oauth/token/accessible-resources"
                headers = {"Authorization": f"Bearer {access_token}"}
                res_response = await client.get(resources_url, headers=headers)
                res_response.raise_for_status()
                resources = res_response.json()
                cloud_id = resources[0].get("id") if resources else None

                insert_response = supabase.table("user_connectors").insert({
                    "user_id": user_id,
                    "service": "jira",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "cloud_id": cloud_id,
                    "expires_at": int(time.time()) + expires_in
                }).execute()

                data = getattr(insert_response, "data", None)
                if not data or len(data) == 0:
                    logging.error("Failed to save Jira tokens")
                else:
                    logging.info(f"Jira tokens saved for user {user_id}")

                background_tasks.add_task(run_master_etl, user_id, "jira")
                logging.info("Jira connected. ETL started!")

                return RedirectResponse(url="http://localhost:3000")

            elif provider == "google":
                token_url = "https://oauth2.googleapis.com/token"
                redirect_uri = f"{APP_BASE_URL}/auth/callback/google"
                payload = {
                    "grant_type": "authorization_code",
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": redirect_uri,
                }

                response = await client.post(token_url, data=payload)
                response.raise_for_status()
                token_data = response.json()

                access_token = token_data.get("access_token")
                refresh_token = token_data.get("refresh_token")
                expires_in = token_data.get("expires_in", 3600)

                insert_response = supabase.table("user_connectors") \
                    .insert({
                        "user_id": user_id,
                        "service": "google",
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "cloud_id": None,
                        "expires_at": int(time.time()) + expires_in
                    }) \
                    .execute()

                data = getattr(insert_response, "data", None)
                if data and len(data) > 0:
                    logging.info(f"Google Tokens SAVED! Record ID: {data[0]['id']}")
                else:
                    logging.error("Failed to save Google tokens")
                    return RedirectResponse(url="http://localhost:3000?error=failed_to_save")

                background_tasks.add_task(run_master_etl, user_id, "google")
                logging.info("Google connected. ETL started!")
                return RedirectResponse(url="http://localhost:3000")

            elif provider == "microsoft":
                parts = state.split("_")
                user_id = parts[1]
                ms_type = parts[2]

                token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
                redirect_uri = f"{APP_BASE_URL}/auth/callback/microsoft"

                payload = {
                    "client_id": MICROSOFT_CLIENT_ID,
                    "client_secret": MICROSOFT_CLIENT_SECRET,
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                }

                response = await client.post(token_url, data=payload)
                response.raise_for_status()
                token_data = response.json()

                access_token = token_data.get("access_token")
                refresh_token = token_data.get("refresh_token")
                expires_in = token_data.get("expires_in", 3600)

                service_map = {
                    "excel": "microsoft-excel",
                    "project": "microsoft-project",
                    "teams": "microsoft-teams"
                }
                service = service_map.get(ms_type, None)

                supabase.table("user_connectors").insert({
                    "user_id": user_id,
                    "service": service,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "cloud_id": None,
                    "expires_at": int(time.time()) + expires_in
                }).execute()

                background_tasks.add_task(run_master_etl, user_id, service)
                return RedirectResponse(url="http://localhost:3000")

            elif provider == "asana":
                parts = state.split("_")
                user_id = parts[1]

                token_url = "https://app.asana.com/-/oauth_token"
                redirect_uri = f"{APP_BASE_URL}/auth/callback/asana"

                payload = {
                    "grant_type": "authorization_code",
                    "client_id": ASANA_CLIENT_ID,
                    "client_secret": ASANA_CLIENT_SECRET,
                    "redirect_uri": redirect_uri,
                    "code": code
                }

                response = await client.post(token_url, data=payload)
                response.raise_for_status()
                token_data = response.json()

                access_token = token_data.get("access_token")
                refresh_token = token_data.get("refresh_token")
                expires_in = token_data.get("expires_in", 3600)

                insert_response = supabase.table("user_connectors").insert({
                    "user_id": user_id,
                    "service": "asana",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "cloud_id": None,
                    "expires_at": int(time.time()) + expires_in
                }).execute()

                data = getattr(insert_response, "data", None)
                if not data:
                    logging.error("Failed to save Asana tokens")
                    return RedirectResponse(url="http://localhost:3000?error=failed_to_save")

                logging.info(f"Asana tokens saved for user {user_id}")
                background_tasks.add_task(run_master_etl, user_id, "asana")
                logging.info("Asana ETL started!")

                return RedirectResponse(url="http://localhost:3000")

        except Exception as e:
            logging.error(f"Error during {provider} callback: {e}", exc_info=True)
            return RedirectResponse(url="http://localhost:3000?error=oauth_failed")

@connect_router.post("/sync/{provider}")
async def sync_service(
    provider: str,
    background_tasks: BackgroundTasks,
    ids: dict = Depends(get_backend_user_id)
):
    """
    Manually triggers an ETL sync for a given provider.
    """
    user_id = ids.get('user_id')

    if not user_id:
        logging.error("Sync attempted without valid user ID.")
        return {"error": "Authentication failed: User ID not found."}

    logging.info(f"Sync initiated by user_id: {user_id} for provider: {provider}")
    background_tasks.add_task(run_master_etl, user_id, provider)

    return {"status": f"Sync scheduled for {provider} for user {user_id}."}