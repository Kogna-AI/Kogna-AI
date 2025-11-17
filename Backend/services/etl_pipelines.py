from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from jira import JIRA
from urllib.parse import quote
import time, os, json, asyncio, httpx
from supabase_connect import get_supabase_manager
from services.embedding_service import embed_and_store_file

supabase = get_supabase_manager().client

async def run_test():
    """
    A simple test function to see if httpx is working.
    """
    print("---  RUNNING TEST FUNCTION ---")
    try:
        test_url = "https://jsonplaceholder.typicode.com/todos/1"
        print(f"Calling test API: {test_url}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(test_url)
            response.raise_for_status()  # Raise error on bad status
            
            data = response.json()
            print("---  TEST SUCCESSFUL ---")
            print(f"API Response: {data}")
            return {"status": "success", "data": data}

    except httpx.HTTPStatusError as e:
        print(f"---  TEST FAILED (HTTP Error) ---")
        print(f"Status Code: {e.response.status_code}")
        print(f"Response: {e.response.text}")
        return {"status": "error", "message": "HTTP Error"}
    except Exception as e:
        print(f"---  TEST FAILED (General Error) ---")
        print(f"Error: {e}")
        return {"status": "error", "message": str(e)}
    
# -------------------------------------------------
# 1. NEW MASTER ETL FUNCTION
# -------------------------------------------------
async def run_master_etl(user_id: str, service: str):
    """
    Selects and runs the correct ETL pipeline based on the service.
    """
    print(f"---  MASTER ETL: Starting sync for {service} for user {user_id} ---")
    
    # 1. Get a valid token for this service
    access_token = await get_valid_tokens(user_id, service)
    if not access_token:
        print(f" MASTER ETL: Could not get valid token for {service}. Aborting.")
        return False
        
    # 2. Select the correct pipeline to run
    success = False
    if service == "jira":
        success = await _run_jira_etl(user_id, access_token) #  Call helper

    elif service == "google":
        success = await _run_google_etl(user_id, access_token)
    #  FUTURE: Add your next provider's ETL
    # elif service == "another_service":
    #     success = await _run_another_service_etl(user_id, access_token)
    
    else:
        print(f" MASTER ETL: No pipeline found for service '{service}'.")
        return False

    if success:
        print(f"---  MASTER ETL: Finished sync for {service} ---")
    else:
        print(f"---  MASTER ETL: Failed sync for {service} ---")
    
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

        #  CHANGED: Select the correct refresh function
        new_token_data = None
        if service == "jira":
            new_token_data = await refresh_jira_token(refresh_token)
        
        elif service == "google":
            new_token_data = await refresh_google_token(refresh_token)

        #  FUTURE: Add your next provider's refresh logic
        # elif service == "another_service":
        #     new_token_data = await refresh_another_service_token(refresh_token)

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
# 3. JIRA-SPECIFIC FUNCTIONS
# -------------------------------------------------
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


async def _run_jira_etl(user_id: str, access_token: str):
    """
    Final ETL function with correct endpoints.
    """
    print(f"--- Starting Jira ETL for user: {user_id} ---")
    
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
            response.raise_for_status()
            
            resources = response.json()
            if not resources:
                print(" No accessible resources found.")
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
            print(f" Authenticated as: {user.get('displayName')}")

            # 3. Fetch issues
            print("Fetching kogna project issues ...")
            jql_query = 'project = "SCRUM" AND created >= -30d ORDER BY created DESC'
            fields_list = "summary,status,assignee,created,updated,description,issuetype,project,reporter"
            search_url = f"{base_url}/search/jql?jql={quote(jql_query)}&maxResults=50&fields={fields_list}"
            
            search_response = await client.get(search_url)
            search_response.raise_for_status()
            
            issues_data = search_response.json()
            issues = issues_data.get('issues', [])
            print(f" Successfully fetched {len(issues)} kogna issues!")

            # 4. Save to bucket
            if issues:
                print("\n--- Inspecting first issue from API ---")
                print(json.dumps(issues[0], indent=2)) 
                print("---------------------------------------\n")

                bucket_name = "Kogna" 
                print(f"Saving {len(issues)} issues to Supabase Storage bucket '{bucket_name}'...")
                issues_json_string = json.dumps(issues, indent=2)
                file_path = f"{user_id}/jira/issues_{int(time.time())}.json"
                issues_bytes = issues_json_string.encode('utf-8')
                
                try:
                    supabase.storage.from_(bucket_name).upload(
                        path=file_path,
                        file=issues_bytes,
                        file_options={"content-type": "application/json;charset=UTF-8"}
                    )
                    print(f" Successfully saved issues to bucket!")
                    print(f"   File path: {file_path}")

                    await embed_and_store_file(user_id, file_path)
                
                except Exception as e:
                    print(f" Error uploading to Supabase Storage: {e}")
            
            print(f"--- Finished Jira ETL for user: {user_id} ---")
            return True

    except httpx.HTTPStatusError as e:
        print(f" API Error {e.response.status_code}: {e.response.text}")
        print(f"Failed URL: {e.request.url}")
        return False
    except Exception as e:
        print(f" ETL Error: {e}")
        import traceback
        traceback.print_exc()
        return False

# -------------------------------------------------
# 4. GOOGLE-SPECIFIC FUNCTIONS
# -------------------------------------------------

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
            return response.json() 
    except httpx.HTTPStatusError as e:
        print(f"Error refreshing Google token: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"Unexpected error refreshing Google token: {e}")
    return None

async def extract_and_save_content(client, user_id, file_id, file_name, mime_type):
    """
    Handles downloading and saving the content of a single file.
    """
    content = None
    file_extension = "txt" # Default
    base_url = "https://www.googleapis.com/drive/v3/files/"
    
    try:
        if mime_type == "application/vnd.google-apps.document":
            # --- Handle Google Docs ---
            export_url = f"{base_url}{file_id}/export?mimeType=text/plain"
            response = await client.get(export_url)
            response.raise_for_status()
            content = response.content # This will be as bytes
            file_extension = "txt"

        elif mime_type == "application/vnd.google-apps.spreadsheet":
            # --- Handle Google Sheets ---
            export_url = f"{base_url}{file_id}/export?mimeType=text/csv"
            response = await client.get(export_url)
            response.raise_for_status()
            content = response.content
            file_extension = "csv"

        elif mime_type == "application/pdf" or mime_type == "text/plain":
            # --- Handle Plain Text and PDFs ---
            download_url = f"{base_url}{file_id}?alt=media"
            response = await client.get(download_url)
            response.raise_for_status()
            content = response.content
            file_extension = "pdf" if mime_type == "application/pdf" else "txt"
            
        else:
            # --- Handle Unsupported Files (like video/quicktime) ---
            print(f"Skipping unsupported file: {file_name} (Type: {mime_type})")
            return # Stop here, do not save anything

        # 3. Save the extracted content to Supabase
        if content:
            bucket_name = "Kogna"
            # We save content in a new 'content' subfolder
            file_path = f"{user_id}/google_drive/content/{file_id}.{file_extension}"
            
            print(f"Saving content for: {file_name}")
            supabase.storage.from_(bucket_name).upload(
                path=file_path,
                file=content, # Upload the raw bytes
                file_options={"content-type": mime_type}
            )

            await embed_and_store_file(user_id, file_path)

    except Exception as e:
        print(f"Error processing file {file_name} (ID: {file_id}): {e}")

async def _run_google_etl(user_id: str, access_token: str):
    """
    Fetches file metadata from Google Drive, handling pagination.
    """
    print(f"--- Starting Google Drive ETL for user: {user_id} ---")
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient(headers=headers) as client:
            
            # --- Add pagination support ---
            all_files_list = []
            page_token = None
            base_list_url = (
                "https://www.googleapis.com/drive/v3/files?"
                "pageSize=100&"
                "orderBy=modifiedTime desc&"
                # We need nextPageToken in the fields list
                "fields=files(id,name,mimeType,createdTime,modifiedTime,webViewLink),nextPageToken"
            )
            
            print("Starting Google Drive file list fetch (with pagination)...")
            
            while True:
                # Construct the URL for the current page
                list_files_url = base_list_url
                if page_token:
                    list_files_url += f"&pageToken={page_token}"
                
                response = await client.get(list_files_url)
                response.raise_for_status()
                
                files_data = response.json()
                files_on_page = files_data.get('files', [])
                all_files_list.extend(files_on_page)
                
                page_token = files_data.get('nextPageToken')
                
                print(f"Fetched {len(files_on_page)} files. Total so far: {len(all_files_list)}")
                
                # If there's no next page token, we're done
                if not page_token:
                    break
            
            # --- END PAGINATION ---

            print(f"Successfully fetched metadata for {len(all_files_list)} Google Drive files!")

            # 2. Loop through each file and extract content
            for file in all_files_list:
                file_id = file.get("id")
                file_name = file.get("name")
                mime_type = file.get("mimeType")

                # This is where we handle the different types
                await extract_and_save_content(client, user_id, file_id, file_name, mime_type)

            print(f"--- Finished Google Drive ETL for user: {user_id} ---")
            return True

    except httpx.HTTPStatusError as e:
        print(f"API Error {e.response.status_code}: {e.response.text}")
        print(f"Failed URL: {e.request.url}")
        return False
    except Exception as e:
        print(f"ETL Error: {e}")
        import traceback
        traceback.print_exc()
        return False