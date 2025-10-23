# Backend/services/etl_pipelines.py
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from jira import JIRA
from urllib.parse import quote
import time, os, json, asyncio, httpx
from supabase_connect import get_supabase_manager

supabase = get_supabase_manager().client

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

        new_token_data = await refresh_jira_token(refresh_token)
        if new_token_data and "access_token" in new_token_data:
            new_expires_at = int(time.time()) + new_token_data.get("expires_in", 3600)
            update_response = supabase.table("user_connectors").update({
                "access_token": new_token_data["access_token"],
                "expires_at": new_expires_at
            }).eq("id", data["id"]).execute()
            print("Token refreshed and updated successfully.")
            return new_token_data["access_token"]
        else:
            print("Failed to refresh token.")
            return None

    return data["access_token"]

async def refresh_jira_token(refresh_token: str):
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

async def run_jira_etl(user_id: str):
    """
    Final ETL function with correct endpoints.
    """
    print(f"--- Starting Jira ETL for user: {user_id} ---")

    # 1. Get a valid token (using your existing function)
    access_token = await get_valid_tokens(user_id, "jira")
    if not access_token:
        print(f"❌ Could not get valid token for {user_id}. Aborting ETL.")
        return False
        
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient(headers=headers) as client:
            # 1. Get cloud_id
            print("Getting cloud_id...")
            resources_url = "https://api.atlassian.com/oauth/token/accessible-resources"
            response = await client.get(resources_url)
            response.raise_for_status()  # <-- Ensure this call worked
            
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
            response.raise_for_status()  # <-- Ensure this call worked
            
            user = response.json()
            print(f"✅ Authenticated as: {user.get('displayName')}")

            

            # 3. ✅ CORRECTED: Fetch issues using the /search/jql endpoint
            print("Fetching kogna project issues ...")
            jql_query = 'project = "SCRUM" AND created >= -30d ORDER BY created DESC'
            
            # --- FIX ---
            # Explicitly request the fields instead of using 'fields=all'
            fields_list = "summary,status,assignee,created,updated,description,issuetype,project,reporter"
            search_url = f"{base_url}/search/jql?jql={quote(jql_query)}&maxResults=50&fields={fields_list}"
            
            search_response = await client.get(search_url)
            search_response.raise_for_status()  # <-- Ensure this call worked
            
            issues_data = search_response.json()
            issues = issues_data.get('issues', [])
            print(f"✅ Successfully fetched {len(issues)} kogna issues!")

            if issues:
                print("\n--- Inspecting first issue from API ---")
                # We need to import json at the top of the file
                print(json.dumps(issues[0], indent=2)) 
                print("---------------------------------------\n")
            # --- END OF DEBUG CODE ---
                bucket_name = "Kogna" # <-- CHANGE THIS to your bucket name
                print(f"Saving {len(issues)} issues to Supabase Storage bucket '{bucket_name}'...")

                # 1. Convert the Python list of issues into a JSON string
                issues_json_string = json.dumps(issues, indent=2)
                
                # 2. Create a unique file name (e.g., jira/issues_12345_1678886400.json)
                file_path = f"jira/issues_{user_id}_{int(time.time())}.json"
                
                # 3. Convert the JSON string to bytes for uploading
                issues_bytes = issues_json_string.encode('utf-8')
                
                # 4. Upload to your bucket
                try:
                    # Make sure you created the bucket in your Supabase dashboard
                    supabase.storage.from_(bucket_name).upload(
                        path=file_path,
                        file=issues_bytes,
                        file_options={"content-type": "application/json;charset=UTF-8"}
                    )
                    
                    print(f"✅ Successfully saved issues to bucket!")
                    print(f"   File path: {file_path}")
                
                except Exception as e:
                    # This often happens if the bucket is private or doesn't exist
                    print(f"❌ Error uploading to Supabase Storage: {e}")
            
            print(f"--- Finished Jira ETL for user: {user_id} ---")
            return True

    except httpx.HTTPStatusError as e:
        # This will now give much clearer errors
        print(f"❌ API Error {e.response.status_code}: {e.response.text}")
        print(f"Failed URL: {e.request.url}")
        return False
    except Exception as e:
        print(f"❌ ETL Error: {e}")
        import traceback
        traceback.print_exc()
        return False