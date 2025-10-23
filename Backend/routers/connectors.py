import os
from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import RedirectResponse
from urllib.parse import quote
import httpx
import logging
import time 

# --- EXACT SAME IMPORTS AS YOUR ETL ---
from services.etl_pipelines import run_jira_etl 
from supabase_connect import get_supabase_manager
supabase = get_supabase_manager().client  # ✅ EXACT SAME!

# --- Environment Variables ---
JIRA_CLIENT_ID = os.getenv("JIRA_CLIENT_ID")
JIRA_CLIENT_SECRET = os.getenv("JIRA_CLIENT_SECRET")
JIRA_REDIRECT_URI = "http://127.0.0.1:8000/auth/callback" 

# --- Routers ---
connect_router = APIRouter(prefix="/connect", tags=["Connectors"])
callback_router = APIRouter(tags=["Connectors"])

@connect_router.get("/jira")
async def connect_to_jira():
    """Initiates OAuth flow"""
    scopes = ["read:jira-work", "read:jira-user", "offline_access"]
    scope = quote(" ".join(scopes))
    state = "your-unique-state-string"
    
    auth_url = (
        f"https://auth.atlassian.com/authorize?"
        f"audience=api.atlassian.com&"
        f"client_id={JIRA_CLIENT_ID}&"
        f"scope={scope}&"
        f"redirect_uri={quote(JIRA_REDIRECT_URI)}&"
        f"state={state}&"
        f"response_type=code&"
        f"prompt=consent"
    )
    return RedirectResponse(url=auth_url)

@callback_router.get("/auth/callback")
async def auth_callback(code: str, state: str, background_tasks: BackgroundTasks):
    """
    Handles Atlassian callback - SAVES TOKENS + TRIGGERS ETL
    """
    async with httpx.AsyncClient() as client:
        try:
            # 1. Exchange code for tokens
            token_url = "https://auth.atlassian.com/oauth/token"
            payload = {
                "grant_type": "authorization_code",
                "client_id": JIRA_CLIENT_ID,
                "client_secret": JIRA_CLIENT_SECRET,
                "code": code,
                "redirect_uri": JIRA_REDIRECT_URI,
            }
            
            response = await client.post(token_url, json=payload)
            response.raise_for_status()
            
            token_data = response.json()
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
            
            if not access_token:
                return {"error": "Access token not provided"}

            logging.info("✅ Successfully received tokens")

            # 2. Get cloud_id
            resources_url = "https://api.atlassian.com/oauth/token/accessible-resources"
            headers = {"Authorization": f"Bearer {access_token}"}
            
            res_response = await client.get(resources_url, headers=headers)
            res_response.raise_for_status()
            
            resources = res_response.json()
            if not resources:
                return {"error": "No Jira sites found"}
            
            cloud_id = resources[0].get("id")
            site_name = resources[0].get("name")
            logging.info(f"✅ Found Jira site: {site_name} (Cloud ID: {cloud_id})")

            # 3. ✅ SAVE TOKENS (EXACT SAME STYLE AS YOUR ETL!)
            user_id = "12345" 
            
            insert_response = supabase.table("user_connectors") \
                .insert({
                    "user_id": user_id,
                    "service": "jira",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "cloud_id": cloud_id,  # ✅ CRITICAL!
                    "expires_at": int(time.time()) + 3600
                }) \
                .execute()
            
            data = getattr(insert_response, "data", None)
            if data and len(data) > 0:
                logging.info(f"✅ Tokens SAVED! Record ID: {data[0]['id']}")
            else:
                logging.error("❌ Failed to save tokens")
                return {"error": "Failed to save connection"}

            # 4. ✅ TRIGGER ETL (CORRECT SYNTAX!)
            background_tasks.add_task(run_jira_etl, user_id)  # ✅ POSITIONAL ARG!
            
            logging.info("🎉 Jira connected. ETL started!")
            return {"status": "Jira connected successfully! ETL started."}
            
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP Error: {e.response.status_code}")
            return {"error": "Failed to exchange token"}
        except Exception as e:
            logging.error(f"Error: {e}", exc_info=True)
            return {"error": "Authentication failed"}