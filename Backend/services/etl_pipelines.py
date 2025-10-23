# Backend/services/etl_pipelines.py
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from jira import JIRA
from urllib.parse import quote
import time, os, json, asyncio, httpx
from supabase_connect import get_supabase_manager

supabase = get_supabase_manager().client

async def run_test():
    """
    A simple test function to see if httpx is working.
    """
    print("--- 🚀 RUNNING TEST FUNCTION ---")
    try:
        test_url = "https://jsonplaceholder.typicode.com/todos/1"
        print(f"Calling test API: {test_url}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(test_url)
            response.raise_for_status()  # Raise error on bad status
            
            data = response.json()
            print("--- ✅ TEST SUCCESSFUL ---")
            print(f"API Response: {data}")
            return {"status": "success", "data": data}

    except httpx.HTTPStatusError as e:
        print(f"--- ❌ TEST FAILED (HTTP Error) ---")
        print(f"Status Code: {e.response.status_code}")
        print(f"Response: {e.response.text}")
        return {"status": "error", "message": "HTTP Error"}
    except Exception as e:
        print(f"--- ❌ TEST FAILED (General Error) ---")
        print(f"Error: {e}")
        return {"status": "error", "message": str(e)}
    
# -------------------------------------------------
# 1. NEW MASTER ETL FUNCTION
# -------------------------------------------------
async def run_master_etl(user_id: str, service: str):
    """
    Selects and runs the correct ETL pipeline based on the service.
    """
    print(f"--- 🚀 MASTER ETL: Starting sync for {service} for user {user_id} ---")
    
    # 1. Get a valid token for this service
    access_token = await get_valid_tokens(user_id, service)
    if not access_token:
        print(f"❌ MASTER ETL: Could not get valid token for {service}. Aborting.")
        return False
        
    # 2. Select the correct pipeline to run
    success = False
    if service == "jira":
        success = await _run_jira_etl(user_id, access_token) # ⚠️ Call helper

    elif service == "google":
        success = await _run_google_etl(user_id, access_token)
    # 📌 FUTURE: Add your next provider's ETL
    # elif service == "google":
    #     success = await _run_google_etl(user_id, access_token)
    
    else:
        print(f"❌ MASTER ETL: No pipeline found for service '{service}'.")
        return False

    if success:
        print(f"--- ✅ MASTER ETL: Finished sync for {service} ---")
    else:
        print(f"--- ❌ MASTER ETL: Failed sync for {service} ---")
    
    return success

# -------------------------------------------------
# 2. TOKEN MANAGEMENT (NOW GENERIC)
# -------------------------------------------------
async def get_valid_tokens(user_id: str, service: str):
    response = supabase.table("user_connectors") \
        .select("*") \
        .eq("user_id", user_id) \
        .eq("service", service) \
        .order("created_at", desc=True) \
        .limit(1) \
        .maybe_single() \
        .execute()

    data = getattr(response, "data", None)
    error = getattr(response, "error", None)
    if error or not data:
        print(f"Error fetching tokens for {user_id}, service {service}: {error}")
        return None

    expires_at = int(data.get("expires_at", 0))
    if int(time.time()) > expires_at:
        print(f"Token for {service} expired. Refreshing...")
        refresh_token = data.get("refresh_token")
        if not refresh_token:
            print("No refresh token found.")
            return None

        # ⚠️ CHANGED: Select the correct refresh function
        new_token_data = None
        if service == "jira":
            new_token_data = await refresh_jira_token(refresh_token)
        
        elif service == "google":
            new_token_data = await refresh_google_token(refresh_token)

        # 📌 FUTURE: Add your next provider's refresh logic
        # elif service == "google":
        #     new_token_data = await refresh_google_token(refresh_token)

        if new_token_data and "access_token" in new_token_data:
            new_expires_at = int(time.time()) + new_token_data.get("expires_in", 3600)
            update_response = supabase.table("user_connectors").update({
                "access_token": new_token_data["access_token"],
                "expires_at": new_expires_at
            }).eq("id", data["id"]).execute()
            print("Token refreshed and updated successfully.")
            return new_token_data["access_token"]
        else:
            print(f"Failed to refresh token for {service}.")
            return None

    return data["access_token"]

# -------------------------------------------------
# 3. JIRA-SPECIFIC FUNCTIONS (UNCHANGED)
# -------------------------------------------------
async def refresh_jira_token(refresh_token: str):
    # ... (This function is unchanged)
    token_url = "https://auth.atlassian.com/oauth/token"
    data = {
        "client_id": os.getenv("JIRA_CLIENT_ID"),
        "client_secret": os.getenv("JIRA_CLIENT_SECRET"),
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                print(f"Unexpected response: {data}")
                return None
            return data
    except httpx.HTTPStatusError as e:
        print(f"Error refreshing Jira token: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"Unexpected error refreshing Jira token: {e}")
    return None


# ⚠️ CHANGED: Renamed to `_run_jira_etl` and accepts `access_token`
async def _run_jira_etl(user_id: str, access_token: str):
    """
    Final ETL function with correct endpoints.
    """
    print(f"--- Starting Jira ETL for user: {user_id} ---")

    # ⚠️ REMOVED: The get_valid_tokens call is now in the master function.
    
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient(headers=headers) as client:
            # 1. Get cloud_id (rest of your code is UNCHANGED)
            print("Getting cloud_id...")
            resources_url = "https://api.atlassian.com/oauth/token/accessible-resources"
            # ...
            # ... (all your existing logic for fetching, logging, and uploading)
            # ... (is perfect and remains the same)
            # ...
            
            response = await client.get(resources_url)
            response.raise_for_status()
            
            resources = response.json()
            if not resources:
                print("❌ No accessible resources found.")
                return False
                
            cloud_id = resources[0]["id"]
            print(f"Using cloud_id: {cloud_id}")
            
            # 2. Authenticate
            print("Authenticating...")
            base_url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3"
            myself_url = f"{base_url}/myself"
            response = await client.get(myself_url)
            response.raise_for_status()
            
            user = response.json()
            print(f"✅ Authenticated as: {user.get('displayName')}")

            # 3. Fetch issues
            print("Fetching kogna project issues ...")
            jql_query = 'project = "SCRUM" AND created >= -30d ORDER BY created DESC'
            fields_list = "summary,status,assignee,created,updated,description,issuetype,project,reporter"
            search_url = f"{base_url}/search/jql?jql={quote(jql_query)}&maxResults=50&fields={fields_list}"
            
            search_response = await client.get(search_url)
            search_response.raise_for_status()
            
            issues_data = search_response.json()
            issues = issues_data.get('issues', [])
            print(f"✅ Successfully fetched {len(issues)} kogna issues!")

            # 4. Save to bucket
            if issues:
                # ... (your debug print) ...
                print("\n--- Inspecting first issue from API ---")
                print(json.dumps(issues[0], indent=2)) 
                print("---------------------------------------\n")

                bucket_name = "Kogna" 
                print(f"Saving {len(issues)} issues to Supabase Storage bucket '{bucket_name}'...")
                issues_json_string = json.dumps(issues, indent=2)
                file_path = f"jira/issues_{user_id}_{int(time.time())}.json"
                issues_bytes = issues_json_string.encode('utf-8')
                
                try:
                    supabase.storage.from_(bucket_name).upload(
                        path=file_path,
                        file=issues_bytes,
                        file_options={"content-type": "application/json;charset=UTF-8"}
                    )
                    print(f"✅ Successfully saved issues to bucket!")
                    print(f"   File path: {file_path}")
                
                except Exception as e:
                    print(f"❌ Error uploading to Supabase Storage: {e}")
            
            print(f"--- Finished Jira ETL for user: {user_id} ---")
            return True

    except httpx.HTTPStatusError as e:
        # ... (error handling is unchanged)
        print(f"❌ API Error {e.response.status_code}: {e.response.text}")
        print(f"Failed URL: {e.request.url}")
        return False
    except Exception as e:
        # ... (error handling is unchanged)
        print(f"❌ ETL Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
async def refresh_google_token(refresh_token: str):
    """Refreshes an expired Google access token."""
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            response.raise_for_status()
            # Google's refresh does NOT return a new refresh_token
            # It returns access_token, expires_in, scope, token_type
            return response.json() 
    except httpx.HTTPStatusError as e:
        print(f"Error refreshing Google token: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"Unexpected error refreshing Google token: {e}")
    return None

async def _run_google_etl(user_id: str, access_token: str):
    """
    Fetches file metadata from Google Drive.
    """
    print(f"--- Starting Google Drive ETL for user: {user_id} ---")
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient(headers=headers) as client:
            # 1. Define API endpoint to list files
            # This fetches the first 100 files, ordered by modified time
            list_files_url = (
                "https://www.googleapis.com/drive/v3/files?"
                "pageSize=100&"
                "orderBy=modifiedTime desc&"
                "fields=files(id,name,mimeType,createdTime,modifiedTime,webViewLink)"
            )
            
            response = await client.get(list_files_url)
            response.raise_for_status()
            
            files_data = response.json()
            files = files_data.get('files', [])
            print(f"✅ Successfully fetched {len(files)} Google Drive files!")

            # 2. Save to bucket
            if files:
                bucket_name = "Kogna" # Using your same bucket
                file_path = f"google_drive/files_{user_id}_{int(time.time())}.json"
                print(f"Saving {len(files)} files to Supabase Storage bucket...")

                files_json_string = json.dumps(files, indent=2)
                files_bytes = files_json_string.encode('utf-8')
                
                try:
                    supabase.storage.from_(bucket_name).upload(
                        path=file_path,
                        file=files_bytes,
                        file_options={"content-type": "application/json;charset=UTF-8"}
                    )
                    print(f"✅ Successfully saved Google files to bucket!")
                    print(f"   File path: {file_path}")
                except Exception as e:
                    print(f"❌ Error uploading to Supabase Storage: {e}")
            
            print(f"--- Finished Google Drive ETL for user: {user_id} ---")
            return True

    except httpx.HTTPStatusError as e:
        print(f"❌ API Error {e.response.status_code}: {e.response.text}")
        print(f"Failed URL: {e.request.url}")
        return False
    except Exception as e:
        print(f"❌ ETL Error: {e}")
        import traceback
        traceback.print_exc()
        return False