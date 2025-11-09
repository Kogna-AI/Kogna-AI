import os
from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from urllib.parse import quote
import httpx
import logging
import time 
from services.etl_pipelines import run_master_etl, run_test
from routers.Authentication import get_backend_user_id

# CHANGED: Import the new 'master' ETL function
from services.etl_pipelines import run_master_etl 
from supabase_connect import get_supabase_manager
supabase = get_supabase_manager().client

# --- Environment Variables ---
JIRA_CLIENT_ID = os.getenv("JIRA_CLIENT_ID")
JIRA_CLIENT_SECRET = os.getenv("JIRA_CLIENT_SECRET")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")

# NEW: Base URL for your app
APP_BASE_URL = "http://127.0.0.1:8000" 

# --- Routers ---
connect_router = APIRouter(prefix="/api/connect", tags=["Connectors"])
callback_router = APIRouter(tags=["Connectors"]) # No prefix - OAuth callback at root level

@connect_router.get("/test")
async def run_simple_test():
    """
    Runs the simple httpx test.
    """
    return await run_test()

# -------------------------------------------------
# 1. GENERIC CONNECT ENDPOINT
# -------------------------------------------------
@connect_router.get("/{provider}")  #CHANGED: Was "/jira"
async def connect_to_service(provider: str):
    """Initiates OAuth flow for a given provider."""
    
    # CRITICAL FIX: The state must include the user_id for the callback to work.
    # We use a timestamp to prevent simple CSRF attacks.
    state = f"auth_{user_id}_{int(time.time())}"
    
    # --- Provider-specific logic ---
    if provider == "jira":
        scopes = ["read:jira-work", "read:jira-user", "offline_access"]
        scope = quote(" ".join(scopes))
        
        #CHANGED: redirect_uri is now dynamic
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
        return JSONResponse({"url": auth_url})

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
        return JSONResponse({"url": auth_url})

    if provider == "excel":
        # Microsoft Graph API - for Excel, OneDrive files
        scopes = [
            "Files.Read.All",
            "Files.ReadWrite.All",
            "User.Read",
            "offline_access"
        ]
        scope = quote(" ".join(scopes))
        redirect_uri = quote(f"{APP_BASE_URL}/auth/callback/excel")

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
        return RedirectResponse(url=auth_url)

    return {"error": "Unknown provider"}

# -------------------------------------------------
# 2. GENERIC CALLBACK ENDPOINT
# -------------------------------------------------
@callback_router.get("/auth/callback/{provider}") #CHANGED: Was "/auth/callback"
async def auth_callback(
    provider: str,  # NEW: We get the provider from the URL
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
        # redirect to homepage if invalid
        return RedirectResponse(url="http://localhost:3000")

    async with httpx.AsyncClient() as client:
        try:
            if provider == "jira":
                # Exchange code for tokens
                token_url = "https://auth.atlassian.com/oauth/token"

                #CHANGED: The redirect_uri must match the one from step 1
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

                # Jira-specific: get cloud_id
                resources_url = "https://api.atlassian.com/oauth/token/accessible-resources"
                headers = {"Authorization": f"Bearer {access_token}"}
                res_response = await client.get(resources_url, headers=headers)
                res_response.raise_for_status()
                resources = res_response.json()
                cloud_id = resources[0].get("id") if resources else None
            
            
                # 3. SAVE TOKENS (This is already generic!)
                insert_response = supabase.table("user_connectors") \
                    .insert({
                        "user_id": user_id,
                        "service": "jira",  #We hard-code "jira" here
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "cloud_id": cloud_id,
                        "expires_at": int(time.time()) + expires_in
                    }) \
                    .execute()
                
                # ... (rest of your insert check logic is fine) ...
                
                # 4.TRIGGER THE *MASTER* ETL
                # CHANGED: Call the master function with the provider
                background_tasks.add_task(run_master_etl, user_id, "jira")
                
                logging.info("Jira connected. ETL started!")
                return {"status": "Jira connected successfully! ETL started."}

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
                
                # ⬇This is the "insert check logic" ⬇
                data = getattr(insert_response, "data", None)
                if data and len(data) > 0:
                    logging.info(f"Google Tokens SAVED! Record ID: {data[0]['id']}")
                else:
                    logging.error("Failed to save Google tokens")
                    return {"error": "Failed to save connection"}
            
                background_tasks.add_task(run_master_etl, user_id, "google")
                
                logging.info("Google connected. ETL started!")
                return {"status": "Google connected successfully! ETL started."}
            # --- END OF NEW BLOCK ---

            if provider == "excel":
                # 1. Exchange code for tokens (Microsoft-specific)
                token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
                redirect_uri = f"{APP_BASE_URL}/auth/callback/excel"

                payload = {
                    "grant_type": "authorization_code",
                    "client_id": MICROSOFT_CLIENT_ID,
                    "client_secret": MICROSOFT_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "scope": "Files.Read.All Files.ReadWrite.All User.Read offline_access"
                }

                response = await client.post(token_url, data=payload)
                response.raise_for_status()
                token_data = response.json()

                access_token = token_data.get("access_token")
                refresh_token = token_data.get("refresh_token")
                expires_in = token_data.get("expires_in", 3600)

                # 2. Save tokens to database
                insert_response = supabase.table("user_connectors") \
                    .insert({
                        "user_id": user_id,
                        "service": "excel",
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "cloud_id": None,
                        "expires_at": int(time.time()) + expires_in
                    }) \
                    .execute()

                # Check if insert was successful
                data = getattr(insert_response, "data", None)
                if data and len(data) > 0:
                    logging.info(f"Excel Tokens SAVED! Record ID: {data[0]['id']}")
                else:
                    logging.error("Failed to save Excel tokens")
                    return {"error": "Failed to save connection"}

                # 3. Trigger ETL pipeline
                background_tasks.add_task(run_master_etl, user_id, "excel")

                logging.info("Excel connected. ETL started!")
                return {"status": "Excel connected successfully! ETL started."}

            else:
                logging.error(f"Unknown provider: {provider}")
                return RedirectResponse(url="http://localhost:3000")

        except Exception as e:
            logging.error(f"Error during {provider} callback: {e}", exc_info=True)
            return RedirectResponse(url="http://localhost:3000")

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