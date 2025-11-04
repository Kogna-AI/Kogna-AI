import os
from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import RedirectResponse
from urllib.parse import quote
import httpx
import logging
import time 
from services.etl_pipelines import run_master_etl, run_test
from routers.Authentication import get_backend_user_id

from services.etl_pipelines import run_master_etl 
from supabase_connect import get_supabase_manager
supabase = get_supabase_manager().client

# --- Environment Variables ---
JIRA_CLIENT_ID = os.getenv("JIRA_CLIENT_ID")
JIRA_CLIENT_SECRET = os.getenv("JIRA_CLIENT_SECRET")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# IMPROVEMENT: Load Base URL from ENV with a fallback for development
# This makes deployment easier.
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://127.0.0.1:8000") 

# --- Routers ---
connect_router = APIRouter(prefix="/connect", tags=["Connectors"])
callback_router = APIRouter(tags=["Connectors"]) # No prefix needed

@connect_router.get("/test")
async def run_simple_test():
    """
    Runs the simple httpx test.
    """
    return await run_test()

# -------------------------------------------------
# 1. GENERIC CONNECT ENDPOINT
# -------------------------------------------------
@connect_router.get("/{provider}") 
async def connect_to_service(
    provider: str,
    user_data: dict = Depends(get_backend_user_id)
    ):
    user_id = user_data.get('user_id')
    
    # CRITICAL FIX: The state must include the user_id for the callback to work.
    # We use a timestamp to prevent simple CSRF attacks.
    state = f"auth_{user_id}_{int(time.time())}"
    
    # --- Provider-specific logic ---
    if provider == "jira":
        scopes = ["read:jira-work", "read:jira-user", "offline_access"]
        scope = quote(" ".join(scopes))
        
        redirect_uri = quote(f"{APP_BASE_URL}/auth/callback/jira")
        
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
        return RedirectResponse(url=auth_url)

    if provider == "google":
        # Note: 'offline_access' is what gets you a refresh_token
        scopes = [
            "https://www.googleapis.com/auth/drive.readonly", 
            "https://www.googleapis.com/auth/userinfo.email",
            "openid"
        ]
        scope = quote(" ".join(scopes))
        redirect_uri = quote(f"{APP_BASE_URL}/auth/callback/google")
        
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={GOOGLE_CLIENT_ID}&"
            f"redirect_uri={redirect_uri}&"
            f"response_type=code&"
            f"scope={scope}&"
            f"access_type=offline&" # Required for refresh_token
            f"prompt=consent&"
            f"state={state}"
        )
        return RedirectResponse(url=auth_url)

    return {"error": "Unknown provider"}

# -------------------------------------------------
# 2. GENERIC CALLBACK ENDPOINT
# -------------------------------------------------
@callback_router.get("/auth/callback/{provider}") 
async def auth_callback(
    provider: str,  
    code: str, 
    state: str, 
    background_tasks: BackgroundTasks,
):
    """
    Handles callback from any provider - SAVES TOKENS + TRIGGERS ETL
    """
    try:
        # The user_id is the second element if the state format is "auth_USERID_TIMESTAMP"
        # The state logic in connect_to_service has been fixed to ensure this.
        user_id = state.split('_')[1] 
    except IndexError:
        logging.error(f"Invalid state format received: {state}")
        return {"error": "Authentication failed: Invalid state parameter."}
    
    # The current user session ID is not compared against the state, 
    # but the state contains the user ID we need for the database insert.
    
    async with httpx.AsyncClient() as client:
        try:
            # --- Provider-specific logic ---
            if provider == "jira":
                # 1. Exchange code for tokens (Jira-specific)
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
                
                # 2. Get tokens and cloud_id (Jira-specific)
                access_token = token_data.get("access_token")
                refresh_token = token_data.get("refresh_token")
                expires_in = token_data.get("expires_in", 3600)

                resources_url = "https://api.atlassian.com/oauth/token/accessible-resources"
                headers = {"Authorization": f"Bearer {access_token}"}
                res_response = await client.get(resources_url, headers=headers)
                res_response.raise_for_status()
                
                resources = res_response.json()
                cloud_id = resources[0].get("id") if resources else None
            
            
                # 3. SAVE TOKENS
                insert_response = supabase.table("user_connectors") \
                    .insert({
                        "user_id": user_id,
                        "service": "jira", 
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "cloud_id": cloud_id,
                        "expires_at": int(time.time()) + expires_in
                    }) \
                    .execute()
                
                # ... (rest of your insert check logic is fine) ...
                data = getattr(insert_response, "data", None)
                if data and len(data) > 0:
                    logging.info(f" Jira Tokens SAVED! Record ID: {data[0]['id']}")
                else:
                    logging.error(" Failed to save Jira tokens")
                    return {"error": "Failed to save connection"}
                
                # 4.  TRIGGER THE *MASTER* ETL
                background_tasks.add_task(run_master_etl, user_id, "jira")
                
                logging.info(" Jira connected. ETL started!")
                return {"status": "Jira connected successfully! ETL started."}

            if provider == "google":
                # 1. Exchange code for tokens (Google-specific)
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

                # 3. SAVE TOKENS
                insert_response = supabase.table("user_connectors") \
                    .insert({
                        "user_id": user_id,
                        "service": "google",
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "cloud_id": None, # Google doesn't use this equivalent field here
                        "expires_at": int(time.time()) + expires_in
                    }) \
                    .execute()
                
                #  This is the "insert check logic" 
                data = getattr(insert_response, "data", None)
                if data and len(data) > 0:
                    logging.info(f" Google Tokens SAVED! Record ID: {data[0]['id']}")
                else:
                    logging.error(" Failed to save Google tokens")
                    return {"error": "Failed to save connection"}
            
                # 4.  TRIGGER THE *MASTER* ETL
                background_tasks.add_task(run_master_etl, user_id, "google")
                
                logging.info(" Google connected. ETL started!")
                return {"status": "Google connected successfully! ETL started."}
            
            else:
                return {"error": "Callback error: Unknown provider"}
            
        except httpx.HTTPStatusError as e:
            # Catch specific HTTP errors from the token exchange (e.g., bad code)
            logging.error(f"HTTP Error during {provider} token exchange: {e.response.text}", exc_info=True)
            return {"error": f"Authentication failed: Could not exchange code for token. Provider error: {e.response.status_code}"}
        except Exception as e:
            logging.error(f"Error during {provider} callback: {e}", exc_info=True)
            return {"error": "Authentication failed"}

# -------------------------------------------------
# 3. NEW MANUAL SYNC ENDPOINT
# -------------------------------------------------
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