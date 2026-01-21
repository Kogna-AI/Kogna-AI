import os
import time
import logging
import httpx
from datetime import datetime, timedelta
from urllib.parse import quote
from typing import List, Optional, Dict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel

from services.etl_pipelines import run_master_etl, run_test
from auth.dependencies import get_backend_user_id
from supabase_connect import get_supabase_manager


supabase = get_supabase_manager().client

# ------------------------------------------------------------------
# Environment
# ------------------------------------------------------------------

JIRA_CLIENT_ID = os.getenv("JIRA_CLIENT_ID")
JIRA_CLIENT_SECRET = os.getenv("JIRA_CLIENT_SECRET")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")

ASANA_CLIENT_ID = os.getenv("ASANA_CLIENT_ID")
ASANA_CLIENT_SECRET = os.getenv("ASANA_CLIENT_SECRET")

APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")
FRONTEND_BASE_URL = "http://localhost:3000"

# ------------------------------------------------------------------
# Models
# ------------------------------------------------------------------

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

# ------------------------------------------------------------------
# Routers
# ------------------------------------------------------------------

connect_router = APIRouter(prefix="/api/connect", tags=["Connectors"])
callback_router = APIRouter(prefix="/api/connect", tags=["Connectors"])

# ------------------------------------------------------------------
# Test
# ------------------------------------------------------------------

@connect_router.get("/test")
async def run_simple_test():
    return await run_test()

# ------------------------------------------------------------------
# Get Connection Status (must be before /{provider} route!)
# ------------------------------------------------------------------

@connect_router.get("/status")
async def get_connection_status(
    ids: dict = Depends(get_backend_user_id),
):
    """
    Get connection status for all connectors.
    Returns a dictionary mapping service names to connection status.
    Status is 'connected' if the connection was updated within the last 30 minutes.
    """
    try:
        user_id = ids.get("user_id")
        if not user_id:
            logging.warning("No user_id found in ids")
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        logging.info(f"Fetching connection status for user: {user_id}")
    except Exception as e:
        logging.error(f"Error getting user_id: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")

    try:
        # Get all user connections
        response = supabase.table("user_connectors").select(
            "service, updated_at, created_at"
        ).eq("user_id", user_id).execute()

        # Calculate 30 minutes ago timestamp
        thirty_minutes_ago = datetime.utcnow() - timedelta(minutes=30)
        
        status_map: Dict[str, dict] = {}
        
        for conn in response.data:
            service = conn.get("service")
            if not service:
                continue
                
            # Parse updated_at timestamp
            updated_at_str = conn.get("updated_at")
            created_at_str = conn.get("created_at")
            
            if updated_at_str:
                try:
                    # Handle both ISO format and database timestamp format
                    if isinstance(updated_at_str, str):
                        # Try parsing ISO format (e.g., "2026-01-15T21:52:13.184097+00:00")
                        if 'T' in updated_at_str or '+' in updated_at_str:
                            # Remove timezone info and parse
                            if '+' in updated_at_str:
                                updated_at_str = updated_at_str.split('+')[0]
                            elif 'Z' in updated_at_str:
                                updated_at_str = updated_at_str.replace('Z', '')
                            
                            # Parse ISO format
                            if '.' in updated_at_str:
                                updated_at = datetime.strptime(
                                    updated_at_str.split('.')[0],
                                    '%Y-%m-%dT%H:%M:%S'
                                )
                            else:
                                updated_at = datetime.fromisoformat(updated_at_str)
                        else:
                            # Parse database timestamp format (e.g., "2026-01-15 21:52:13.184097")
                            parts = updated_at_str.split('.')
                            updated_at = datetime.strptime(
                                parts[0],
                                '%Y-%m-%d %H:%M:%S'
                            )
                    else:
                        updated_at = updated_at_str
                    
                    # Make timezone-naive for comparison
                    if hasattr(updated_at, 'tzinfo') and updated_at.tzinfo:
                        updated_at = updated_at.replace(tzinfo=None)
                    
                    # Calculate next reconnect time (30 minutes after last update)
                    next_reconnect = updated_at + timedelta(minutes=30)
                    
                    # Check if updated within last 30 minutes
                    if updated_at >= thirty_minutes_ago:
                        status_map[service] = {
                            "status": "connected",
                            "connected_at": conn.get("updated_at"),
                            "created_at": conn.get("created_at"),
                            "next_reconnect": next_reconnect.isoformat()
                        }
                    else:
                        status_map[service] = {
                            "status": "available",
                            "connected_at": conn.get("updated_at"),
                            "created_at": conn.get("created_at"),
                            "next_reconnect": None
                        }
                except Exception as e:
                    logging.error(f"Error parsing timestamp for {service}: {e}")
                    status_map[service] = {
                        "status": "available",
                        "connected_at": None,
                        "created_at": None,
                        "next_reconnect": None
                    }
            else:
                status_map[service] = {
                    "status": "available",
                    "connected_at": None,
                    "created_at": None,
                    "next_reconnect": None
                }
        
        logging.info(f"Returning connection status: {status_map}")
        return {"connections": status_map}
    
    except Exception as e:
        logging.error(f"Error fetching connection status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch connection status: {str(e)}")

# ------------------------------------------------------------------
# OAuth Start (Authenticated)
# ------------------------------------------------------------------

@connect_router.get("/{provider}")
async def connect_to_service(
    provider: str,
    ids: dict = Depends(get_backend_user_id)
):
    user_id = ids.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    state = f"oauth_{user_id}_{int(time.time())}"

    if provider == "jira":
        scope = quote("read:jira-work read:jira-user offline_access")
        redirect_uri = f"{APP_BASE_URL}/api/connect/callback/jira"

        return JSONResponse({
            "url": (
                "https://auth.atlassian.com/authorize?"
                f"audience=api.atlassian.com&"
                f"client_id={JIRA_CLIENT_ID}&"
                f"scope={scope}&"
                f"redirect_uri={redirect_uri}&"
                f"state={state}&"
                f"response_type=code&"
                f"prompt=consent"
            )
        })

    if provider == "google":
        scope = quote(
            "openid https://www.googleapis.com/auth/userinfo.email "
            "https://www.googleapis.com/auth/drive.readonly"
        )
        redirect_uri = f"{APP_BASE_URL}/api/connect/callback/google"

        return JSONResponse({
            "url": (
                "https://accounts.google.com/o/oauth2/v2/auth?"
                f"client_id={GOOGLE_CLIENT_ID}&"
                f"redirect_uri={redirect_uri}&"
                f"response_type=code&"
                f"scope={scope}&"
                f"access_type=offline&"
                f"prompt=consent&"
                f"state={state}"
            )
        })

    if provider == "microsoft":
        scope = quote("User.Read Files.Read Files.ReadWrite Sites.Read.All offline_access")
        redirect_uri = f"{APP_BASE_URL}/api/connect/callback/microsoft"

        return JSONResponse({
            "url": (
                "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
                f"client_id={MICROSOFT_CLIENT_ID}&"
                f"response_type=code&"
                f"redirect_uri={redirect_uri}&"
                f"scope={scope}&"
                f"state={state}&"
                f"prompt=consent"
            )
        })

    if provider == "asana":
        scope = quote("tasks:read projects:read users:read workspaces:read")
        redirect_uri = f"{APP_BASE_URL}/api/connect/callback/asana"

        return JSONResponse({
            "url": (
                "https://app.asana.com/-/oauth_authorize?"
                f"client_id={ASANA_CLIENT_ID}&"
                f"redirect_uri={quote(redirect_uri)}&"
                f"response_type=code&"
                f"scope={scope}&"
                f"state={state}&"
                f"prompt=consent"
            )
        })

    raise HTTPException(status_code=400, detail="Unknown provider")

# ------------------------------------------------------------------
# OAuth Callback (Public)
# ------------------------------------------------------------------

@callback_router.get("/callback/{provider}")
async def auth_callback(
    provider: str,
    code: str,
    state: str,
    background_tasks: BackgroundTasks,
):
    try:
        user_id = state.split("_")[1]
    except Exception:
        logging.error(f"Invalid OAuth state: {state}")
        return RedirectResponse(f"{FRONTEND_BASE_URL}/login")

    async with httpx.AsyncClient() as client:

        if provider == "jira":
            token = (
                await client.post(
                    "https://auth.atlassian.com/oauth/token",
                    json={
                        "grant_type": "authorization_code",
                        "client_id": JIRA_CLIENT_ID,
                        "client_secret": JIRA_CLIENT_SECRET,
                        "code": code,
                        "redirect_uri": f"{APP_BASE_URL}/api/connect/callback/jira",
                    },
                )
            ).json()

            # Upsert to prevent duplicate key errors on re-connection
            supabase.table("user_connectors").upsert({
                "user_id": user_id,
                "service": "jira",
                "access_token": token["access_token"],
                "refresh_token": token.get("refresh_token"),
                "expires_at": int(time.time()) + token.get("expires_in", 3600),
            }, on_conflict="user_id, service").execute()

            background_tasks.add_task(run_master_etl, user_id, "jira")

        elif provider == "google":
            token = (
                await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "grant_type": "authorization_code",
                        "client_id": GOOGLE_CLIENT_ID,
                        "client_secret": GOOGLE_CLIENT_SECRET,
                        "code": code,
                        "redirect_uri": f"{APP_BASE_URL}/api/connect/callback/google",
                    },
                )
            ).json()

            supabase.table("user_connectors").upsert({
                "user_id": user_id,
                "service": "google",
                "access_token": token["access_token"],
                "refresh_token": token.get("refresh_token"),
                "expires_at": int(time.time()) + token.get("expires_in", 3600),
            }, on_conflict="user_id, service").execute()

            background_tasks.add_task(run_master_etl, user_id, "google")

        elif provider == "microsoft":
            token = (
                await client.post(
                    "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                    data={
                        "client_id": MICROSOFT_CLIENT_ID,
                        "client_secret": MICROSOFT_CLIENT_SECRET,
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": f"{APP_BASE_URL}/api/connect/callback/microsoft",
                    },
                )
            ).json()

            supabase.table("user_connectors").upsert({
                "user_id": user_id,
                "service": "microsoft",
                "access_token": token["access_token"],
                "refresh_token": token.get("refresh_token"),
                "expires_at": int(time.time()) + token.get("expires_in", 3600),
            }, on_conflict="user_id, service").execute()

            background_tasks.add_task(run_master_etl, user_id, "microsoft")

        elif provider == "asana":
            token = (
                await client.post(
                    "https://app.asana.com/-/oauth_token",
                    data={
                        "grant_type": "authorization_code",
                        "client_id": ASANA_CLIENT_ID,
                        "client_secret": ASANA_CLIENT_SECRET,
                        "code": code,
                        "redirect_uri": f"{APP_BASE_URL}/api/connect/callback/asana",
                    },
                )
            ).json()

            supabase.table("user_connectors").upsert({
                "user_id": user_id,
                "service": "asana",
                "access_token": token["access_token"],
                "refresh_token": token.get("refresh_token"),
                "expires_at": int(time.time()) + token.get("expires_in", 3600),
            }, on_conflict="user_id, service").execute()

            background_tasks.add_task(run_master_etl, user_id, "asana")

    return RedirectResponse(
        f"{FRONTEND_BASE_URL}/oauth/success?provider={provider}"
    )

# ------------------------------------------------------------------
# Manual Sync
# ------------------------------------------------------------------

@connect_router.post("/sync/{provider}")
async def sync_service(
    provider: str,
    background_tasks: BackgroundTasks,
    ids: dict = Depends(get_backend_user_id),
):
    user_id = ids.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    background_tasks.add_task(run_master_etl, user_id, provider)
    return {"status": "sync_started"}
    
