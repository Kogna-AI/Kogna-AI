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
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")

# ------------------------------------------------------------------
# Helper: Normalize Provider Names
# ------------------------------------------------------------------

def normalize_provider(provider: str) -> tuple[str, str]:
    """
    Normalize provider names for OAuth and ETL routing.
    
    Returns:
        tuple: (oauth_provider, etl_service)
        - oauth_provider: Used for OAuth flow (microsoft, google, jira, asana)
        - etl_service: Used for ETL routing (microsoft-excel, microsoft-teams, etc)
    """
    provider = provider.lower()
    
    # Microsoft services all use same OAuth but different ETL
    microsoft_services = {
        "microsoft": "microsoft-excel",  # Default to excel
        "microsoft-excel": "microsoft-excel",
        "microsoft-teams": "microsoft-teams",
        "microsoft-project": "microsoft-project",
    }
    
    if provider in microsoft_services:
        return ("microsoft", microsoft_services[provider])
    
    # Other services have 1:1 mapping
    service_map = {
        "jira": ("jira", "jira"),
        "google": ("google", "google"),
        "asana": ("asana", "asana"),
    }
    
    if provider in service_map:
        return service_map[provider]
    
    raise ValueError(f"Unknown provider: {provider}")

# ------------------------------------------------------------------
# Helper: Save or Update Connector
# ------------------------------------------------------------------

def save_or_update_connector(user_id: str, service: str, token: dict):
    """
    Save or update connector tokens in database
    """
    # Check if connector already exists
    existing = supabase.table("user_connectors")\
        .select("id")\
        .eq("user_id", user_id)\
        .eq("service", service)\
        .execute()

    connector_data = {
        "user_id": user_id,
        "service": service,
        "access_token": token["access_token"],
        "refresh_token": token.get("refresh_token"),
        "expires_at": int(time.time()) + token.get("expires_in", 3600),
    }

    if existing.data:
        # Update existing connector
        supabase.table("user_connectors")\
            .update(connector_data)\
            .eq("user_id", user_id)\
            .eq("service", service)\
            .execute()
        logging.info(f"Updated {service} connector for user {user_id}")
    else:
        # Insert new connector
        supabase.table("user_connectors")\
            .insert(connector_data)\
            .execute()
        logging.info(f"Created new {service} connector for user {user_id}")

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

    try:
        oauth_provider, etl_service = normalize_provider(provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    state = f"oauth_{user_id}_{etl_service}_{int(time.time())}"

    if oauth_provider == "jira":
        if not JIRA_CLIENT_ID or not JIRA_CLIENT_SECRET:
            raise HTTPException(status_code=500, detail="Jira OAuth not configured")
        
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

    elif oauth_provider == "google":
        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
            raise HTTPException(status_code=500, detail="Google OAuth not configured")
        
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

    elif oauth_provider == "microsoft":
        if not MICROSOFT_CLIENT_ID or not MICROSOFT_CLIENT_SECRET:
            raise HTTPException(status_code=500, detail="Microsoft OAuth not configured")
        
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

    elif oauth_provider == "asana":
        if not ASANA_CLIENT_ID or not ASANA_CLIENT_SECRET:
            raise HTTPException(status_code=500, detail="Asana OAuth not configured")
        
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

@callback_router.get("/callback/{oauth_provider}")
async def auth_callback(
    oauth_provider: str,
    code: str,
    state: str,
    background_tasks: BackgroundTasks,
):
    # Extract user_id and etl_service from state
    try:
        parts = state.split("_")
        user_id = parts[1]
        etl_service = parts[2]  # microsoft-excel, microsoft-teams, etc
        logging.info(f"OAuth callback for {oauth_provider}, user_id: {user_id}, service: {etl_service}")
    except Exception as e:
        logging.error(f"Invalid OAuth state: {state}, error: {e}")
        return RedirectResponse(f"{FRONTEND_BASE_URL}/connectors?error=invalid_state")

    async with httpx.AsyncClient() as client:

        if oauth_provider == "jira":
            if not JIRA_CLIENT_ID or not JIRA_CLIENT_SECRET:
                logging.error("Jira OAuth credentials not configured")
                return RedirectResponse(
                    f"{FRONTEND_BASE_URL}/connectors?error=jira&message=not_configured"
                )
            
            try:
                logging.info(f"Exchanging Jira authorization code for token")
                response = await client.post(
                    "https://auth.atlassian.com/oauth/token",
                    json={
                        "grant_type": "authorization_code",
                        "client_id": JIRA_CLIENT_ID,
                        "client_secret": JIRA_CLIENT_SECRET,
                        "code": code,
                        "redirect_uri": f"{APP_BASE_URL}/api/connect/callback/jira",
                    },
                )
                
                logging.info(f"Jira token response status: {response.status_code}")
                
                if response.status_code != 200:
                    logging.error(f"Jira token exchange failed: {response.text}")
                    return RedirectResponse(
                        f"{FRONTEND_BASE_URL}/connectors?error=jira&message=token_exchange_failed"
                    )
                
                token = response.json()
                
                if "error" in token:
                    logging.error(f"Jira OAuth error: {token}")
                    return RedirectResponse(
                        f"{FRONTEND_BASE_URL}/connectors?error=jira&message={token.get('error', 'unknown')}"
                    )
                
                if "access_token" not in token:
                    logging.error(f"No access_token in Jira response: {token}")
                    return RedirectResponse(
                        f"{FRONTEND_BASE_URL}/connectors?error=jira&message=missing_token"
                    )

            # Upsert to prevent duplicate key errors on re-connection
            supabase.table("user_connectors").upsert({
                "user_id": user_id,
                "service": "jira",
                "access_token": token["access_token"],
                "refresh_token": token.get("refresh_token"),
                "expires_at": int(time.time()) + token.get("expires_in", 3600),
            }, on_conflict="user_id, service").execute()

        elif oauth_provider == "google":
            if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
                logging.error("Google OAuth credentials not configured")
                return RedirectResponse(
                    f"{FRONTEND_BASE_URL}/connectors?error=google&message=not_configured"
                )
            
            try:
                logging.info(f"Exchanging Google authorization code for token")
                response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "grant_type": "authorization_code",
                        "client_id": GOOGLE_CLIENT_ID,
                        "client_secret": GOOGLE_CLIENT_SECRET,
                        "code": code,
                        "redirect_uri": f"{APP_BASE_URL}/api/connect/callback/google",
                    },
                )
                
                logging.info(f"Google token response status: {response.status_code}")
                
                if response.status_code != 200:
                    logging.error(f"Google token exchange failed: {response.text}")
                    return RedirectResponse(
                        f"{FRONTEND_BASE_URL}/connectors?error=google&message=token_exchange_failed"
                    )
                
                token = response.json()
                
                if "error" in token:
                    logging.error(f"Google OAuth error: {token}")
                    return RedirectResponse(
                        f"{FRONTEND_BASE_URL}/connectors?error=google&message={token.get('error', 'unknown')}"
                    )
                
                if "access_token" not in token:
                    logging.error(f"No access_token in Google response: {token}")
                    return RedirectResponse(
                        f"{FRONTEND_BASE_URL}/connectors?error=google&message=missing_token"
                    )

            supabase.table("user_connectors").upsert({
                "user_id": user_id,
                "service": "google",
                "access_token": token["access_token"],
                "refresh_token": token.get("refresh_token"),
                "expires_at": int(time.time()) + token.get("expires_in", 3600),
            }, on_conflict="user_id, service").execute()

        elif oauth_provider == "microsoft":
            if not MICROSOFT_CLIENT_ID or not MICROSOFT_CLIENT_SECRET:
                logging.error("Microsoft OAuth credentials not configured")
                return RedirectResponse(
                    f"{FRONTEND_BASE_URL}/connectors?error=microsoft&message=not_configured"
                )
            
            try:
                logging.info(f"Exchanging Microsoft authorization code for token")
                response = await client.post(
                    "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                    data={
                        "client_id": MICROSOFT_CLIENT_ID,
                        "client_secret": MICROSOFT_CLIENT_SECRET,
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": f"{APP_BASE_URL}/api/connect/callback/microsoft",
                    },
                )
                
                logging.info(f"Microsoft token response status: {response.status_code}")
                
                if response.status_code != 200:
                    logging.error(f"Microsoft token exchange failed: {response.text}")
                    return RedirectResponse(
                        f"{FRONTEND_BASE_URL}/connectors?error=microsoft&message=token_exchange_failed"
                    )
                
                token = response.json()
                
                if "error" in token:
                    logging.error(f"Microsoft OAuth error: {token}")
                    return RedirectResponse(
                        f"{FRONTEND_BASE_URL}/connectors?error=microsoft&message={token.get('error', 'unknown')}"
                    )
                
                if "access_token" not in token:
                    logging.error(f"No access_token in Microsoft response: {token}")
                    return RedirectResponse(
                        f"{FRONTEND_BASE_URL}/connectors?error=microsoft&message=missing_token"
                    )

            supabase.table("user_connectors").upsert({
                "user_id": user_id,
                "service": "microsoft",
                "access_token": token["access_token"],
                "refresh_token": token.get("refresh_token"),
                "expires_at": int(time.time()) + token.get("expires_in", 3600),
            }, on_conflict="user_id, service").execute()

        elif oauth_provider == "asana":
            if not ASANA_CLIENT_ID or not ASANA_CLIENT_SECRET:
                logging.error("Asana OAuth credentials not configured")
                return RedirectResponse(
                    f"{FRONTEND_BASE_URL}/connectors?error=asana&message=not_configured"
                )
            
            try:
                logging.info(f"Exchanging Asana authorization code for token")
                response = await client.post(
                    "https://app.asana.com/-/oauth_token",
                    data={
                        "grant_type": "authorization_code",
                        "client_id": ASANA_CLIENT_ID,
                        "client_secret": ASANA_CLIENT_SECRET,
                        "code": code,
                        "redirect_uri": f"{APP_BASE_URL}/api/connect/callback/asana",
                    },
                )
                
                logging.info(f"Asana token response status: {response.status_code}")
                
                if response.status_code != 200:
                    logging.error(f"Asana token exchange failed: {response.text}")
                    return RedirectResponse(
                        f"{FRONTEND_BASE_URL}/connectors?error=asana&message=token_exchange_failed"
                    )
                
                token = response.json()
                
                if "error" in token:
                    logging.error(f"Asana OAuth error: {token}")
                    return RedirectResponse(
                        f"{FRONTEND_BASE_URL}/connectors?error=asana&message={token.get('error', 'unknown')}"
                    )
                
                if "access_token" not in token:
                    logging.error(f"No access_token in Asana response: {token}")
                    return RedirectResponse(
                        f"{FRONTEND_BASE_URL}/connectors?error=asana&message=missing_token"
                    )

            supabase.table("user_connectors").upsert({
                "user_id": user_id,
                "service": "asana",
                "access_token": token["access_token"],
                "refresh_token": token.get("refresh_token"),
                "expires_at": int(time.time()) + token.get("expires_in", 3600),
            }, on_conflict="user_id, service").execute()

            background_tasks.add_task(run_master_etl, user_id, "asana")

    # Redirect to connectors page with success message
    return RedirectResponse(
        f"{FRONTEND_BASE_URL}/connectors?connected={etl_service}"
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

    try:
        _, etl_service = normalize_provider(provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    background_tasks.add_task(run_master_etl, user_id, etl_service)
    return {"status": "sync_started"}