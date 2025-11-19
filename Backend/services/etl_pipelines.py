from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from jira import JIRA
from urllib.parse import quote
import time, os, json, asyncio, httpx
from supabase_connect import get_supabase_manager
from services.embedding_service import embed_and_store_file
from typing import Optional, Dict, List
import logging

supabase = get_supabase_manager().client
logging.basicConfig(level=logging.INFO)

# =================================================================
# CONSTANTS
# =================================================================
MAX_FILE_SIZE = 50_000_000  # 50MB max file size
RATE_LIMIT_DELAY = 0.1  # 100ms between requests
BATCH_SIZE = 10  # Process 10 files, then pause
TOKEN_REFRESH_BUFFER = 300  # Refresh if expiring within 5 minutes

# =================================================================
# PROGRESS TRACKING
# =================================================================

async def create_sync_job(user_id: str, service: str) -> Optional[str]:
    """Creates a sync job record and returns job_id"""
    try:
        response = supabase.table("sync_jobs").insert({
            "user_id": user_id,
            "service": service,
            "status": "running",
            "started_at": int(time.time()),
            "progress": "0/0",
            "files_processed": 0
        }).execute()
        
        if response.data:
            job_id = response.data[0]['id']
            logging.info(f" Created sync job {job_id} for {service}")
            return job_id
        return None
    except Exception as e:
        logging.error(f"Failed to create sync job: {e}")
        return None

async def update_sync_progress(user_id: str, service: str, **updates):
    """Updates sync job progress"""
    try:
        supabase.table("sync_jobs") \
            .update(updates) \
            .eq("user_id", user_id) \
            .eq("service", service) \
            .eq("status", "running") \
            .execute()
    except Exception as e:
        logging.error(f"Failed to update sync progress: {e}")

async def complete_sync_job(user_id: str, service: str, success: bool, files_count: int = 0, error: str = None):
    """Marks sync job as completed or failed"""
    try:
        updates = {
            "status": "completed" if success else "failed",
            "finished_at": int(time.time()),
            "files_processed": files_count
        }
        if error:
            updates["error_message"] = str(error)[:500]
        
        supabase.table("sync_jobs") \
            .update(updates) \
            .eq("user_id", user_id) \
            .eq("service", service) \
            .eq("status", "running") \
            .execute()
        
        status = " COMPLETED" if success else " FAILED"
        logging.info(f"{status} sync job for {service} ({files_count} files)")
    except Exception as e:
        logging.error(f"Failed to complete sync job: {e}")

# =================================================================
# TOKEN MANAGEMENT
# =================================================================

async def ensure_valid_token(user_id: str, service: str) -> Optional[str]:
    """
    Gets a valid token, refreshing if necessary.
    Checks if token is expiring within 5 minutes.
    """
    try:
        response = supabase.table("user_connectors") \
            .select("*") \
            .eq("user_id", user_id) \
            .eq("service", service) \
            .order("created_at", desc=True) \
            .limit(1) \
            .maybe_single() \
            .execute()

        data = getattr(response, "data", None)
        if not data:
            logging.error(f"No connector found for {service}")
            return None

        expires_at = int(data.get("expires_at", 0))
        current_time = int(time.time())
        
        # Refresh if expiring within buffer time
        if current_time + TOKEN_REFRESH_BUFFER > expires_at:
            logging.info(f" Token expiring soon for {service}. Refreshing...")
            refresh_token = data.get("refresh_token")
            
            if not refresh_token:
                logging.error("No refresh token available")
                return None

            # Select refresh function based on service
            new_token_data = None
            if service == "jira":
                new_token_data = await refresh_jira_token(refresh_token)
            elif service == "google":
                new_token_data = await refresh_google_token(refresh_token)
            # Add more services here

            if new_token_data and "access_token" in new_token_data:
                new_expires_at = current_time + new_token_data.get("expires_in", 3600)
                
                supabase.table("user_connectors").update({
                    "access_token": new_token_data["access_token"],
                    "expires_at": new_expires_at
                }).eq("id", data["id"]).execute()
                
                logging.info(" Token refreshed successfully")
                return new_token_data["access_token"]
            else:
                logging.error(f"Failed to refresh token for {service}")
                return None

        return data["access_token"]
        
    except Exception as e:
        logging.error(f"Error ensuring valid token: {e}")
        return None

async def refresh_jira_token(refresh_token: str) -> Optional[Dict]:
    """Refreshes Jira access token"""
    token_url = "https://auth.atlassian.com/oauth/token"
    data = {
        "client_id": os.getenv("JIRA_CLIENT_ID"),
        "client_secret": os.getenv("JIRA_CLIENT_SECRET"),
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(token_url, data=data)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logging.error(f"Error refreshing Jira token: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        logging.error(f"Unexpected error refreshing Jira token: {e}")
    return None

async def refresh_google_token(refresh_token: str) -> Optional[Dict]:
    """Refreshes Google access token"""
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(token_url, data=data)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logging.error(f"Error refreshing Google token: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        logging.error(f"Unexpected error refreshing Google token: {e}")
    return None

# =================================================================
# FILE UPLOAD HELPERS
# =================================================================

async def safe_upload_to_bucket(
    bucket_name: str, 
    file_path: str, 
    content: bytes, 
    mime_type: str,
    enable_versioning: bool = True
) -> bool:
    """
    Safely uploads file to Supabase Storage with change detection and versioning.
    
    Versioning Strategy:
    - If enable_versioning=True: Creates timestamped versions (file_v1732014000.json)
    - If enable_versioning=False: Overwrites with _latest.json
    - Always keeps a "latest" pointer for quick access
    
    This allows tracking changes over time while maintaining easy access to current data.
    """
    import hashlib
    
    try:
        # Generate content hash for change detection
        content_hash = hashlib.sha256(content).hexdigest()[:16]
        
        # Split file path to create versioned path
        path_parts = file_path.rsplit('/', 1)
        if len(path_parts) == 2:
            directory = path_parts[0]
            filename = path_parts[1]
        else:
            directory = ""
            filename = file_path
        
        # Remove extension
        name_parts = filename.rsplit('.', 1)
        base_name = name_parts[0]
        extension = name_parts[1] if len(name_parts) == 2 else ""
        
        if enable_versioning:
            # Create versioned path with timestamp
            timestamp = int(time.time())
            versioned_filename = f"{base_name}_v{timestamp}.{extension}" if extension else f"{base_name}_v{timestamp}"
            versioned_path = f"{directory}/{versioned_filename}" if directory else versioned_filename
            
            # Also create/update a "latest" pointer
            latest_filename = f"{base_name}_latest.{extension}" if extension else f"{base_name}_latest"
            latest_path = f"{directory}/{latest_filename}" if directory else latest_filename
            
            # Upload versioned file
            logging.info(f" Uploading versioned file: {versioned_path}")
            version_response = supabase.storage.from_(bucket_name).upload(
                path=versioned_path,
                file=content,
                file_options={"content-type": mime_type}
            )
            
            if hasattr(version_response, 'error') and version_response.error:
                logging.error(f" Versioned upload failed: {version_response.error}")
                return False
            
            # Update latest pointer (with upsert)
            logging.info(f" Updating latest pointer: {latest_path}")
            latest_response = supabase.storage.from_(bucket_name).upload(
                path=latest_path,
                file=content,
                file_options={"content-type": mime_type, "upsert": "true"}
            )
            
            if hasattr(latest_response, 'error') and latest_response.error:
                # Latest pointer failed, but versioned succeeded
                logging.warning(f"  Latest pointer update failed, but version saved")
            
            logging.info(f" Uploaded: {versioned_path} (hash: {content_hash})")
            return True
        
        else:
            # No versioning - just use upsert
            upload_response = supabase.storage.from_(bucket_name).upload(
                path=file_path,
                file=content,
                file_options={"content-type": mime_type, "upsert": "true"}
            )
            
            if hasattr(upload_response, 'error') and upload_response.error:
                logging.error(f" Upload failed: {upload_response.error}")
                return False
            
            logging.info(f" Uploaded: {file_path}")
            return True
        
    except Exception as e:
        error_str = str(e).lower()
        
        if "already exists" in error_str or "duplicate" in error_str:
            try:
                logging.info(f"  File exists, updating: {file_path}")
                update_response = supabase.storage.from_(bucket_name).update(
                    path=file_path,
                    file=content,
                    file_options={"content-type": mime_type}
                )
                
                if hasattr(update_response, 'error') and update_response.error:
                    logging.error(f" Update failed: {update_response.error}")
                    return False
                
                logging.info(f" Updated: {file_path}")
                return True
            except Exception as update_error:
                logging.error(f" Error updating file: {update_error}")
                return False
        else:
            logging.error(f" Error uploading {file_path}: {e}")
            return False

# =================================================================
# EMBEDDING QUEUE (Async Processing)
# =================================================================

embedding_queue = []

async def queue_embedding(user_id: str, file_path: str):
    """Adds file to embedding queue for background processing"""
    embedding_queue.append({
        "user_id": user_id,
        "file_path": file_path,
        "queued_at": time.time()
    })
    logging.info(f" Queued for embedding: {file_path}")

async def process_embedding_queue_batch():
    """
    Processes a batch of embeddings from the queue.
    Call this periodically or after ETL completes.
    """
    if not embedding_queue:
        return
    
    logging.info(f" Processing {len(embedding_queue)} embeddings...")
    
    while embedding_queue:
        item = embedding_queue.pop(0)
        try:
            await embed_and_store_file(item["user_id"], item["file_path"])
            await asyncio.sleep(0.5)  # Rate limit embeddings
        except Exception as e:
            logging.error(f" Embedding failed for {item['file_path']}: {e}")

# =================================================================
# MASTER ETL FUNCTION
# =================================================================

async def run_master_etl(user_id: str, service: str):
    """
    Main ETL orchestrator with full error handling and progress tracking.
    """
    logging.info(f"{'='*60}")
    logging.info(f" MASTER ETL: Starting sync for {service} (user: {user_id})")
    logging.info(f"{'='*60}")
    
    job_id = await create_sync_job(user_id, service)
    
    try:
        # Get valid token
        access_token = await ensure_valid_token(user_id, service)
        if not access_token:
            raise ValueError(f"No valid token for {service}")
        
        # Route to correct ETL
        success = False
        files_count = 0
        
        if service == "jira":
            success, files_count = await _run_jira_etl(user_id, access_token)
        elif service == "google":
            success, files_count = await _run_google_etl(user_id, access_token)
        else:
            raise ValueError(f"Unknown service: {service}")
        
        # Complete sync job
        await complete_sync_job(user_id, service, success, files_count)
        
        # Process embeddings in background
        if success and embedding_queue:
            logging.info(f" Processing {len(embedding_queue)} embeddings...")
            asyncio.create_task(process_embedding_queue_batch())
        
        return success
        
    except Exception as e:
        logging.error(f" MASTER ETL FAILED for {service}: {e}")
        import traceback
        traceback.print_exc()
        
        await complete_sync_job(user_id, service, False, 0, str(e))
        return False

# =================================================================
# JIRA ETL
# =================================================================

async def _run_jira_etl(user_id: str, access_token: str) -> tuple[bool, int]:
    """
    Jira ETL with proper error handling and progress tracking.
    Returns: (success, files_count)
    """
    logging.info(f"--- Starting Jira ETL for user: {user_id} ---")
    
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient(headers=headers, timeout=60.0) as client:
            # 1. Get cloud_id
            logging.info(" Getting cloud_id...")
            resources_url = "https://api.atlassian.com/oauth/token/accessible-resources"
            
            response = await client.get(resources_url)
            response.raise_for_status()
            
            resources = response.json()
            if not resources:
                logging.error(" No accessible resources found")
                return False, 0
                
            cloud_id = resources[0]["id"]
            logging.info(f" Using cloud_id: {cloud_id}")
            
            # 2. Authenticate
            base_url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3"
            myself_url = f"{base_url}/myself"
            
            # Refresh token if needed before major API call
            access_token = await ensure_valid_token(user_id, "jira")
            if not access_token:
                raise ValueError("Token refresh failed during ETL")
            
            response = await client.get(myself_url)
            response.raise_for_status()
            
            user = response.json()
            logging.info(f" Authenticated as: {user.get('displayName')}")

            # 3. Get all projects (not hardcoded)
            logging.info(" Fetching all projects...")
            projects_url = f"{base_url}/project"
            projects_response = await client.get(projects_url)
            projects_response.raise_for_status()
            
            projects = projects_response.json()
            logging.info(f" Found {len(projects)} projects")
            
            await update_sync_progress(user_id, "jira", progress=f"0/{len(projects)} projects")
            
            # 4. Fetch issues from all projects
            all_issues = []
            bucket_name = "Kogna"
            
            for idx, project in enumerate(projects):
                project_key = project.get('key')
                project_name = project.get('name')
                
                logging.info(f"📊 Fetching issues from {project_name} ({project_key})...")
                
                # Fetch recent issues from this project
                jql_query = f'project = "{project_key}" AND created >= -30d ORDER BY created DESC'
                fields_list = "summary,status,assignee,created,updated,description,issuetype,project,reporter"
                search_url = f"{base_url}/search/jql?jql={quote(jql_query)}&maxResults=50&fields={fields_list}"
                
                search_response = await client.get(search_url)
                search_response.raise_for_status()
                
                issues_data = search_response.json()
                issues = issues_data.get('issues', [])
                
                if issues:
                    logging.info(f"    Found {len(issues)} issues")
                    all_issues.extend(issues)
                    
                    # Save per-project file WITH VERSIONING
                    issues_json = json.dumps(issues, indent=2)
                    file_path = f"{user_id}/jira/{project_key}_issues.json"
                    issues_bytes = issues_json.encode('utf-8')
                    
                    upload_success = await safe_upload_to_bucket(
                        bucket_name, 
                        file_path, 
                        issues_bytes, 
                        "application/json",
                        enable_versioning=True  # Track changes over time
                    )
                    
                    if upload_success:
                        # Queue LATEST version for embedding
                        latest_path = f"{user_id}/jira/{project_key}_issues_latest.json"
                        await queue_embedding(user_id, latest_path)
                
                await update_sync_progress(user_id, "jira", progress=f"{idx+1}/{len(projects)} projects")
                await asyncio.sleep(RATE_LIMIT_DELAY)  # Rate limiting
            
            # 5. Save combined file WITH VERSIONING
            if all_issues:
                combined_json = json.dumps(all_issues, indent=2)
                file_path = f"{user_id}/jira/all_issues.json"
                combined_bytes = combined_json.encode('utf-8')
                
                await safe_upload_to_bucket(
                    bucket_name, 
                    file_path, 
                    combined_bytes, 
                    "application/json",
                    enable_versioning=True
                )
                
                # Queue latest version for embedding
                latest_path = f"{user_id}/jira/all_issues_latest.json"
                await queue_embedding(user_id, latest_path)
            
            logging.info(f"{'='*60}")
            logging.info(f" Finished Jira ETL: {len(all_issues)} total issues from {len(projects)} projects")
            logging.info(f"{'='*60}")
            
            return True, len(projects) + 1  # Project files + combined file

    except httpx.HTTPStatusError as e:
        logging.error(f" API Error {e.response.status_code}: {e.response.text}")
        logging.error(f"Failed URL: {e.request.url}")
        return False, 0
    except Exception as e:
        logging.error(f" ETL Error: {e}")
        import traceback
        traceback.print_exc()
        return False, 0

# =================================================================
# GOOGLE DRIVE ETL
# =================================================================

async def extract_and_save_content(
    client: httpx.AsyncClient, 
    user_id: str, 
    file_id: str, 
    file_name: str, 
    mime_type: str,
    file_size: int
) -> bool:
    """
    Downloads and saves content of a single Google Drive file.
    Returns True if successful.
    """
    # Skip folders and shortcuts
    if mime_type in ["application/vnd.google-apps.folder", "application/vnd.google-apps.shortcut"]:
        logging.info(f"  Skipping folder/shortcut: {file_name}")
        return False
    
    # Skip files that are too large
    if file_size > MAX_FILE_SIZE:
        logging.warning(f"  Skipping large file: {file_name} ({file_size / 1_000_000:.1f}MB)")
        return False
    
    content = None
    file_extension = "txt"
    base_url = "https://www.googleapis.com/drive/v3/files/"
    
    try:
        if mime_type == "application/vnd.google-apps.document":
            export_url = f"{base_url}{file_id}/export?mimeType=text/plain"
            response = await client.get(export_url)
            response.raise_for_status()
            content = response.content
            file_extension = "txt"

        elif mime_type == "application/vnd.google-apps.spreadsheet":
            export_url = f"{base_url}{file_id}/export?mimeType=text/csv"
            response = await client.get(export_url)
            response.raise_for_status()
            content = response.content
            file_extension = "csv"

        elif mime_type in ["application/pdf", "text/plain"]:
            download_url = f"{base_url}{file_id}?alt=media"
            response = await client.get(download_url)
            response.raise_for_status()
            content = response.content
            file_extension = "pdf" if mime_type == "application/pdf" else "txt"
        else:
            logging.info(f"  Skipping unsupported type: {file_name} ({mime_type})")
            return False

        # Save content WITH VERSIONING
        if content:
            bucket_name = "Kogna"
            file_path = f"{user_id}/google_drive/content/{file_id}.{file_extension}"
            
            upload_success = await safe_upload_to_bucket(
                bucket_name, 
                file_path, 
                content, 
                mime_type,
                enable_versioning=True  # Track document changes over time
            )
            
            if upload_success:
                # Queue latest version for embedding
                path_parts = file_path.rsplit('.', 1)
                base_path = path_parts[0]
                extension = path_parts[1] if len(path_parts) == 2 else ""
                latest_path = f"{base_path}_latest.{extension}" if extension else f"{base_path}_latest"
                
                await queue_embedding(user_id, latest_path)
                return True
        
        return False

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 403:
            logging.warning(f"  Access denied: {file_name}")
        else:
            logging.error(f" HTTP Error processing {file_name}: {e.response.status_code}")
        return False
    except Exception as e:
        logging.error(f" Error processing {file_name}: {e}")
        return False

async def _run_google_etl(user_id: str, access_token: str) -> tuple[bool, int]:
    """
    Google Drive ETL with pagination, rate limiting, and progress tracking.
    Returns: (success, files_count)
    """
    logging.info(f"--- Starting Google Drive ETL for user: {user_id} ---")
    
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient(headers=headers, timeout=60.0) as client:
            # Fetch all files with pagination
            all_files_list = []
            page_token = None
            base_list_url = (
                "https://www.googleapis.com/drive/v3/files?"
                "pageSize=100&"
                "orderBy=modifiedTime desc&"
                "fields=files(id,name,mimeType,size,createdTime,modifiedTime,webViewLink),nextPageToken"
            )
            
            logging.info(" Fetching file list from Google Drive (with pagination)...")
            
            page_num = 0
            while True:
                page_num += 1
                list_files_url = base_list_url
                if page_token:
                    list_files_url += f"&pageToken={page_token}"
                
                # Refresh token if needed
                access_token = await ensure_valid_token(user_id, "google")
                if not access_token:
                    raise ValueError("Token refresh failed during pagination")
                
                response = await client.get(list_files_url)
                response.raise_for_status()
                
                files_data = response.json()
                files_on_page = files_data.get('files', [])
                all_files_list.extend(files_on_page)
                
                logging.info(f"   Page {page_num}: {len(files_on_page)} files (Total: {len(all_files_list)})")
                
                page_token = files_data.get('nextPageToken')
                if not page_token:
                    break
                
                await asyncio.sleep(RATE_LIMIT_DELAY)
            
            logging.info(f" Found {len(all_files_list)} total files")
            await update_sync_progress(user_id, "google", progress=f"0/{len(all_files_list)} files")
            
            # Process files with rate limiting
            processed_count = 0
            successful_count = 0
            
            for idx, file in enumerate(all_files_list):
                file_id = file.get("id")
                file_name = file.get("name")
                mime_type = file.get("mimeType")
                file_size = int(file.get("size", 0))
                
                success = await extract_and_save_content(
                    client, user_id, file_id, file_name, mime_type, file_size
                )
                
                if success:
                    successful_count += 1
                
                processed_count += 1
                
                # Update progress every 10 files
                if processed_count % 10 == 0:
                    await update_sync_progress(
                        user_id, "google", 
                        progress=f"{processed_count}/{len(all_files_list)} files",
                        files_processed=successful_count
                    )
                
                # Rate limiting: pause after every batch
                if (idx + 1) % BATCH_SIZE == 0:
                    logging.info(f"⏸️  Processed {processed_count} files. Brief pause...")
                    await asyncio.sleep(1)
                else:
                    await asyncio.sleep(RATE_LIMIT_DELAY)
            
            logging.info(f"{'='*60}")
            logging.info(f" Finished Google Drive ETL: {successful_count}/{len(all_files_list)} files processed")
            logging.info(f"{'='*60}")
            
            return True, successful_count

    except httpx.HTTPStatusError as e:
        logging.error(f" API Error {e.response.status_code}: {e.response.text}")
        logging.error(f"Failed URL: {e.request.url}")
        return False, 0
    except Exception as e:
        logging.error(f" ETL Error: {e}")
        import traceback
        traceback.print_exc()
        return False, 0

# =================================================================
# TEST FUNCTION
# =================================================================

async def run_test():
    """Simple test function to verify httpx is working"""
    logging.info("---  RUNNING TEST FUNCTION ---")
    try:
        test_url = "https://jsonplaceholder.typicode.com/todos/1"
        logging.info(f"Calling test API: {test_url}")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(test_url)
            response.raise_for_status()
            
            data = response.json()
            logging.info("---  TEST SUCCESSFUL ---")
            logging.info(f"API Response: {data}")
            return {"status": "success", "data": data}

    except Exception as e:
        logging.error(f"---  TEST FAILED ---")
        logging.error(f"Error: {e}")
        return {"status": "error", "message": str(e)}