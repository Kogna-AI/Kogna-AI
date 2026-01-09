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
# HELPER FUNCTIONS - KPI Extraction
# =================================================================

# Cache for organization lookups to avoid repeated queries
_org_cache = {}

async def get_organization_id_for_user(user_id: str) -> Optional[str]:
    """
    Looks up organization ID from users table with caching
    Returns organization_id (UUID) or None
    """
    # Check cache first
    if user_id in _org_cache:
        return _org_cache[user_id]

    try:
        response = supabase.table("users") \
            .select("organization_id") \
            .eq("id", user_id) \
            .maybe_single() \
            .execute()

        if response.data:
            org_id = response.data.get('organization_id')
            _org_cache[user_id] = org_id
            return org_id
        return None
    except Exception as e:
        logging.error(f"Failed to get organization_id for user {user_id}: {e}")
        return None

async def save_connector_kpi(
    user_id: str,
    organization_id: str,
    connector_type: str,
    source_id: str,
    kpi_category: str,
    kpi_name: str,
    kpi_value: any,
    kpi_unit: Optional[str] = None,
    source_name: Optional[str] = None,
    sync_job_id: Optional[str] = None,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None
) -> Optional[Dict]:
    """
    Inserts a KPI into the connector_kpis table

    Args:
        user_id: UUID of the user
        organization_id: UUID of the organization
        connector_type: Type of connector (jira, google_drive, asana, etc.)
        source_id: Identifier of the source (project ID, file ID, etc.)
        kpi_category: Category (velocity, burndown, completion_rate, financial, etc.)
        kpi_name: Name of the KPI
        kpi_value: Value (will be converted to JSONB)
        kpi_unit: Optional unit of measurement
        source_name: Optional human-readable source name
        sync_job_id: Optional UUID linking to sync job
        period_start: Optional ISO timestamp for KPI period start
        period_end: Optional ISO timestamp for KPI period end

    Returns:
        Dictionary with KPI record (including 'id') if successful, None otherwise
    """
    try:
        # Convert kpi_value to proper JSONB structure
        if isinstance(kpi_value, (dict, list)):
            jsonb_value = kpi_value
        elif isinstance(kpi_value, (int, float)):
            jsonb_value = {"value": kpi_value, "type": "numeric"}
        elif isinstance(kpi_value, str):
            jsonb_value = {"value": kpi_value, "type": "string"}
        elif isinstance(kpi_value, bool):
            jsonb_value = {"value": kpi_value, "type": "boolean"}
        else:
            jsonb_value = {"value": str(kpi_value), "type": "unknown"}

        kpi_data = {
            "user_id": user_id,
            "organization_id": organization_id,
            "connector_type": connector_type,
            "source_id": source_id,
            "kpi_category": kpi_category,
            "kpi_name": kpi_name,
            "kpi_value": jsonb_value,
            "kpi_unit": kpi_unit,
            "source_name": source_name
        }

        if sync_job_id:
            kpi_data["sync_job_id"] = sync_job_id
        if period_start:
            kpi_data["period_start"] = period_start
        if period_end:
            kpi_data["period_end"] = period_end

        # Upsert based on unique constraint and return the record
        result = supabase.table("connector_kpis").upsert(kpi_data).execute()

        if result.data and len(result.data) > 0:
            return result.data[0]
        return None

    except Exception as e:
        logging.error(f"Failed to save KPI {kpi_name} for {source_id}: {e}")
        return None


async def queue_kpi_for_embedding(kpi_record: Dict):
    """
    Queues a KPI for embedding generation and storage.
    This runs asynchronously to not block ETL pipeline.

    Args:
        kpi_record: Complete KPI record from connector_kpis table
                    Must contain: id, user_id, organization_id, connector_type,
                    source_id, kpi_name, kpi_value, kpi_category, kpi_unit,
                    source_name, extracted_at (or created_at)
    """
    try:
        from services.kpi_summary_service import generate_kpi_summary_text
        from services.embedding_service import embed_and_store_kpi_summary

        # Extract required fields
        kpi_id = kpi_record.get('id')
        user_id = kpi_record.get('user_id')
        organization_id = kpi_record.get('organization_id')
        connector_type = kpi_record.get('connector_type')
        source_id = kpi_record.get('source_id')

        if not all([kpi_id, user_id, organization_id, connector_type, source_id]):
            logging.warning(f"KPI record missing required fields for embedding: {kpi_record}")
            return
1
        # Prepare KPI data dict for summary generation
        kpi_data = {
            'kpi_name': kpi_record.get('kpi_name'),
            'kpi_category': kpi_record.get('kpi_category'),
            'kpi_value': kpi_record.get('kpi_value'),
            'kpi_unit': kpi_record.get('kpi_unit'),
            'source_name': kpi_record.get('source_name', source_id),
            'extracted_at': kpi_record.get('extracted_at') or kpi_record.get('created_at'),
            'period_start': kpi_record.get('period_start'),
            'period_end': kpi_record.get('period_end')
        }

        # Generate natural language summary
        logging.info(f"Generating summary for KPI {kpi_id}: {kpi_data['kpi_name']}")
        summary_text = await generate_kpi_summary_text(
            kpi_data=kpi_data,
            organization_id=organization_id,
            connector_type=connector_type,
            source_id=source_id,
            include_trends=True
        )

        # Prepare metadata
        metadata = {
            'connector_type': connector_type,
            'source_id': source_id,
            'source_name': kpi_record.get('source_name'),
            'kpi_name': kpi_record.get('kpi_name'),
            'kpi_category': kpi_re1cord.get('kpi_category')
        }

        # Embed and store
        logging.info(f"Embedding KPI {kpi_id}")
        success = await embed_and_store_kpi_summary(
            user_id=user_id,
            organization_id=organization_id,
            kpi_id=kpi_id,
            summary_text=summary_text,1
            metadata=metadata
        )

        if success:
            logging.info(f"✓ KPI {kpi_id} successfully embedded")
        else:
            logging.warning(f"✗ Failed to embed KPI {kpi_id}")

    except Exception as e:
        logging.error(f"Failed to queue KPI for embedding: {e}")
        # Don't raise - embedding failure shouldn't break KPI save
        import traceback
        traceback.print_exc()


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
            elif service in ["microsoft-excel", "microsoft-project", "microsoft-teams"]:
                new_token_data = await refresh_microsoft_token(refresh_token)
            elif service == "asana":
                new_token_data = await refresh_asana_token(refresh_token)

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

async def refresh_microsoft_token(refresh_token: str) -> Optional[Dict]:
    """Refreshes Microsoft access token"""
    token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    data = {
        "client_id": os.getenv("MICROSOFT_CLIENT_ID"),
        "client_secret": os.getenv("MICROSOFT_CLIENT_SECRET"),
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(token_url, data=data)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logging.error(f"Error refreshing Microsoft token: {e}")
        return None

async def refresh_asana_token(refresh_token: str) -> Optional[Dict]:
    """Refreshes Asana access token"""
    token_url = "https://app.asana.com/-/oauth_token"
    data = {
        "client_id": os.getenv("ASANA_CLIENT_ID"),
        "client_secret": os.getenv("ASANA_CLIENT_SECRET"),
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(token_url, data=data)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logging.error(f"Error refreshing Asana token: {e}")
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
        elif service == "microsoft-excel":
            success, files_count = await _run_microsoft_excel_etl(user_id, access_token)
        elif service == "microsoft-teams":
            success, files_count = await _run_microsoft_teams_etl(user_id, access_token)
        elif service == "microsoft-project":
            success, files_count = await _run_microsoft_project_etl(user_id, access_token)
        elif service == "asana":
            success, files_count = await _run_asana_etl(user_id, access_token)
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

async def _run_jira_etl(user_id: str, access_token: str, sync_job_id: Optional[str] = None) -> tuple[bool, int]:
    """
    Enhanced Jira ETL with KPI metrics extraction
    Extracts: issues, projects, sprint data, velocity, team metrics, and dashboard KPIs
    Returns: (success, files_count)
    """
    logging.info(f"--- Starting Jira ETL for user: {user_id} ---")

    # Get organization_id for KPI tracking
    organization_id = await get_organization_id_for_user(user_id)
    kpi_count = 0  # Track total KPIs extracted
    kpi_start_time = time.time()  # Track extraction time

    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient(headers=headers, timeout=60.0) as client:
            # 1. Get cloud_id
            logging.info("Getting cloud_id...")
            resources_url = "https://api.atlassian.com/oauth/token/accessible-resources"
            
            response = await client.get(resources_url)
            response.raise_for_status()
            
            resources = response.json()
            if not resources:
                logging.error("No accessible resources found")
                return False, 0
                
            cloud_id = resources[0]["id"]
            logging.info(f"Using cloud_id: {cloud_id}")
            
            # 2. Authenticate
            base_url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3"
            myself_url = f"{base_url}/myself"
            
            access_token = await ensure_valid_token(user_id, "jira")
            if not access_token:
                raise ValueError("Token refresh failed during ETL")
            
            response = await client.get(myself_url)
            response.raise_for_status()
            
            user = response.json()
            logging.info(f"Authenticated as: {user.get('displayName')}")

            # 3. Get all projects
            logging.info("Fetching all projects...")
            projects_url = f"{base_url}/project"
            projects_response = await client.get(projects_url)
            projects_response.raise_for_status()
            
            projects = projects_response.json()
            logging.info(f"Found {len(projects)} projects")
            
            await update_sync_progress(user_id, "jira", progress=f"0/{len(projects)} projects")
            
            # 4. Initialize data structures
            all_issues = []
            all_kpis = {
                'overview': {},
                'projects': []
            }
            bucket_name = "Kogna"
            
            # 5. Process each project
            for idx, project in enumerate(projects):
                project_key = project.get('key')
                project_name = project.get('name')
                project_id = project.get('id')
                
                logging.info(f"Processing project: {project_name} ({project_key})...")
                
                # Fetch issues (last 90 days for better metrics)
                jql_query = f'project = "{project_key}" AND created >= -90d ORDER BY created DESC'
                fields_list = "summary,status,assignee,created,updated,description,issuetype,project,reporter,priority,timetracking,sprint"
                search_url = f"{base_url}/search/jql?jql={quote(jql_query)}&maxResults=100&fields={fields_list}"
                
                search_response = await client.get(search_url)
                search_response.raise_for_status()
                
                issues_data = search_response.json()
                issues = issues_data.get('issues', [])
                total_issues = issues_data.get('total', 0)
                
                if issues:
                    logging.info(f"   Found {len(issues)} issues (of {total_issues} total)")
                    all_issues.extend(issues)
                    
                    # Calculate KPIs for this project
                    project_kpis = await calculate_project_kpis(
                        client, base_url, project_key, project_name, issues,
                        user_id=user_id,
                        organization_id=organization_id,
                        sync_job_id=sync_job_id,
                        save_to_db=True
                    )

                    all_kpis['projects'].append(project_kpis)
                    kpi_count += 6  # We save 6 KPIs per project
                    
                    # Save per-project issues
                    issues_json = json.dumps(issues, indent=2)
                    file_path = f"{user_id}/jira/projects/{project_key}_issues.json"
                    issues_bytes = issues_json.encode('utf-8')
                    
                    await safe_upload_to_bucket(
                        bucket_name, 
                        file_path, 
                        issues_bytes, 
                        "application/json",
                        enable_versioning=True
                    )
                    
                    latest_path = f"{user_id}/jira/projects/{project_key}_issues_latest.json"
                    await queue_embedding(user_id, latest_path)
                    
                    # Save per-project KPIs
                    kpi_json = json.dumps(project_kpis, indent=2)
                    kpi_path = f"{user_id}/jira/projects/{project_key}_kpis.json"
                    
                    await safe_upload_to_bucket(
                        bucket_name,
                        kpi_path,
                        kpi_json.encode('utf-8'),
                        "application/json",
                        enable_versioning=True
                    )
                
                await update_sync_progress(user_id, "jira", progress=f"{idx+1}/{len(projects)} projects")
                await asyncio.sleep(RATE_LIMIT_DELAY)
            
            # 6. Calculate overall KPIs
            all_kpis['overview'] = calculate_overall_kpis(all_issues, projects)
            
            # 7. Try to get sprint/agile metrics (if available)
            try:
                sprint_metrics = await get_sprint_metrics(client, base_url, projects)
                all_kpis['sprint_metrics'] = sprint_metrics
            except Exception as e:
                logging.warning(f"Could not fetch sprint metrics: {e}")
            
            # 8. Save combined files
            if all_issues:
                # Save all issues
                combined_json = json.dumps(all_issues, indent=2)
                file_path = f"{user_id}/jira/all_issues.json"
                
                await safe_upload_to_bucket(
                    bucket_name, 
                    file_path, 
                    combined_json.encode('utf-8'), 
                    "application/json",
                    enable_versioning=True
                )
                
                latest_path = f"{user_id}/jira/all_issues_latest.json"
                await queue_embedding(user_id, latest_path)
            
            # Save all KPIs
            kpis_json = json.dumps(all_kpis, indent=2)
            kpis_path = f"{user_id}/jira/kpis_dashboard.json"

            await safe_upload_to_bucket(
                bucket_name,
                kpis_path,
                kpis_json.encode('utf-8'),
                "application/json",
                enable_versioning=True
            )

            # Also save as kpis_latest.json for the dashboard
            kpis_latest_path = f"{user_id}/jira/kpis_latest.json"
            await safe_upload_to_bucket(
                bucket_name,
                kpis_latest_path,
                kpis_json.encode('utf-8'),
                "application/json",
                enable_versioning=True
            )

            await queue_embedding(user_id, kpis_latest_path)

            # Calculate KPI extraction metrics
            kpi_extraction_time_ms = int((time.time() - kpi_start_time) * 1000)

            logging.info(f"{'='*60}")
            logging.info(f"Finished Jira ETL: {len(all_issues)} issues, {len(projects)} projects")
            logging.info(f"KPIs extracted: {kpi_count} KPIs saved to database")
            logging.info(f"KPI extraction time: {kpi_extraction_time_ms}ms")
            logging.info(f"{'='*60}")

            # Update sync job with KPI metrics if sync_job_id provided
            if sync_job_id:
                try:
                    supabase.table("sync_jobs").update({
                        "kpis_extracted": kpi_count,
                        "kpi_extraction_time_ms": kpi_extraction_time_ms
                    }).eq("id", sync_job_id).execute()
                except Exception as e:
                    logging.error(f"Failed to update sync job KPI metrics: {e}")

            return True, len(projects) + 2  # Projects + combined + KPIs

    except httpx.HTTPStatusError as e:
        logging.error(f"API Error {e.response.status_code}: {e.response.text}")
        logging.error(f"Failed URL: {e.request.url}")
        return False, 0
    except Exception as e:
        logging.error(f"ETL Error: {e}")
        import traceback
        traceback.print_exc()
        return False, 0


async def calculate_project_kpis(
    client: httpx.AsyncClient,
    base_url: str,
    project_key: str,
    project_name: str,
    issues: list,
    user_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    sync_job_id: Optional[str] = None,
    save_to_db: bool = True
) -> dict:
    """
    Calculate KPI metrics for a project
    Similar to what's shown in Jira dashboard
    Now also saves KPIs to the database if user_id and organization_id are provided
    """
    from datetime import datetime, timedelta
    
    now = datetime.now()
    last_7_days = now - timedelta(days=7)
    last_30_days = now - timedelta(days=30)
    
    # Status counts
    status_counts = {
        'done': 0,
        'in_progress': 0,
        'to_do': 0,
        'total': len(issues)
    }
    
    # Activity counts (last 7 days)
    activity_7_days = {
        'completed': 0,
        'updated': 0,
        'created': 0,
        'due_soon': 0
    }
    
    # Type breakdown
    type_counts = {}
    
    # Priority breakdown
    priority_counts = {
        'highest': 0,
        'high': 0,
        'medium': 0,
        'low': 0,
        'lowest': 0
    }
    
    # Assignee workload
    assignee_counts = {}
    
    for issue in issues:
        fields = issue.get('fields', {})
        
        # Status
        status = fields.get('status', {})
        status_name = status.get('name', '').lower()
        status_category = status.get('statusCategory', {}).get('key', '')
        
        if status_category == 'done':
            status_counts['done'] += 1
        elif status_category == 'indeterminate':
            status_counts['in_progress'] += 1
        else:
            status_counts['to_do'] += 1
        
        # Issue type
        issue_type = fields.get('issuetype', {}).get('name', 'Unknown')
        type_counts[issue_type] = type_counts.get(issue_type, 0) + 1
        
        # Priority
        priority = fields.get('priority', {})
        if priority:
            priority_name = priority.get('name', '').lower()
            if priority_name in priority_counts:
                priority_counts[priority_name] += 1
        
        # Assignee
        assignee = fields.get('assignee', {})
        if assignee:
            assignee_name = assignee.get('displayName', 'Unassigned')
            assignee_counts[assignee_name] = assignee_counts.get(assignee_name, 0) + 1
        else:
            assignee_counts['Unassigned'] = assignee_counts.get('Unassigned', 0) + 1
        
        # Activity (last 7 days)
        try:
            created = datetime.fromisoformat(fields.get('created', '').replace('Z', '+00:00'))
            updated = datetime.fromisoformat(fields.get('updated', '').replace('Z', '+00:00'))
            
            if created >= last_7_days:
                activity_7_days['created'] += 1
            
            if updated >= last_7_days:
                activity_7_days['updated'] += 1
            
            if status_category == 'done' and updated >= last_7_days:
                activity_7_days['completed'] += 1
        except:
            pass
    
    # Calculate percentages
    total = status_counts['total'] or 1
    status_percentages = {
        'done': round((status_counts['done'] / total) * 100, 1),
        'in_progress': round((status_counts['in_progress'] / total) * 100, 1),
        'to_do': round((status_counts['to_do'] / total) * 100, 1)
    }
    
    # Sort assignees by workload
    top_assignees = sorted(
        assignee_counts.items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:5]
    
    # Sort types
    sorted_types = sorted(
        type_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    kpis = {
        'project_key': project_key,
        'project_name': project_name,
        'total_work_items': total,
        'status_overview': {
            'counts': status_counts,
            'percentages': status_percentages
        },
        'recent_activity_7_days': activity_7_days,
        'types_of_work': {
            'breakdown': sorted_types,
            'total_types': len(type_counts)
        },
        'priority_breakdown': priority_counts,
        'team_workload': {
            'top_assignees': top_assignees,
            'total_assignees': len([a for a in assignee_counts.keys() if a != 'Unassigned'])
        }
    }

    # Save KPIs to database if enabled and user info is provided
    if save_to_db and user_id and organization_id:
        try:
            period_end = now.isoformat()
            period_start = last_7_days.isoformat()

            # Save velocity metrics
            await save_connector_kpi(
                user_id=user_id,
                organization_id=organization_id,
                connector_type="jira",
                source_id=project_key,
                source_name=project_name,
                kpi_category="velocity",
                kpi_name="issues_completed_7_days",
                kpi_value=activity_7_days['completed'],
                kpi_unit="issues",
                sync_job_id=sync_job_id,
                period_start=period_start,
                period_end=period_end
            )

            # Calculate average cycle time (simplified - using days)
            cycle_time_days = round(7 / max(activity_7_days['completed'], 1), 2)
            await save_connector_kpi(
                user_id=user_id,
                organization_id=organization_id,
                connector_type="jira",
                source_id=project_key,
                source_name=project_name,
                kpi_category="velocity",
                kpi_name="average_cycle_time_days",
                kpi_value=cycle_time_days,
                kpi_unit="days",
                sync_job_id=sync_job_id,
                period_start=period_start,
                period_end=period_end
            )

            # Save burndown/completion metrics
            await save_connector_kpi(
                user_id=user_id,
                organization_id=organization_id,
                connector_type="jira",
                source_id=project_key,
                source_name=project_name,
                kpi_category="burndown",
                kpi_name="completion_percentage",
                kpi_value=status_percentages['done'],
                kpi_unit="percentage",
                sync_job_id=sync_job_id
            )

            # Save workload metrics
            active_assignees = len([a for a in assignee_counts.keys() if a != 'Unassigned'])
            await save_connector_kpi(
                user_id=user_id,
                organization_id=organization_id,
                connector_type="jira",
                source_id=project_key,
                source_name=project_name,
                kpi_category="productivity",
                kpi_name="active_assignees",
                kpi_value=active_assignees,
                kpi_unit="people",
                sync_job_id=sync_job_id
            )

            await save_connector_kpi(
                user_id=user_id,
                organization_id=organization_id,
                connector_type="jira",
                source_id=project_key,
                source_name=project_name,
                kpi_category="productivity",
                kpi_name="unassigned_count",
                kpi_value=assignee_counts.get('Unassigned', 0),
                kpi_unit="issues",
                sync_job_id=sync_job_id
            )

            # Save priority metrics
            high_priority = priority_counts.get('highest', 0) + priority_counts.get('high', 0)
            await save_connector_kpi(
                user_id=user_id,
                organization_id=organization_id,
                connector_type="jira",
                source_id=project_key,
                source_name=project_name,
                kpi_category="quality",
                kpi_name="high_priority_count",
                kpi_value=high_priority,
                kpi_unit="issues",
                sync_job_id=sync_job_id
            )

            logging.info(f"✓ Saved 6 KPIs for project {project_key}")

            # Queue KPIs for embedding (async, non-blocking)
            # Fetch the most recent KPIs for this project and trigger embedding
            try:
                recent_kpis = supabase.table("connector_kpis").select("*").eq("organization_id", organization_id).eq("connector_type", "jira").eq("source_id", project_key).order("created_at", desc=True).limit(6).execute()
                if recent_kpis.data:
                    for kpi_record in recent_kpis.data:
                        asyncio.create_task(queue_kpi_for_embedding(kpi_record))
                    logging.info(f"✓ Queued {len(recent_kpis.data)} KPIs for embedding")
            except Exception as embed_error:
                logging.warning(f"Failed to queue KPIs for embedding: {embed_error}")

        except Exception as e:
            logging.error(f"Failed to save KPIs for project {project_key}: {e}")

    return kpis


def calculate_overall_kpis(all_issues: list, projects: list) -> dict:
    """
    Calculate organization-wide KPIs across all projects
    """
    from datetime import datetime, timedelta
    
    now = datetime.now()
    last_7_days = now - timedelta(days=7)
    
    total_issues = len(all_issues)
    
    # Overall status
    done = sum(1 for i in all_issues if i.get('fields', {}).get('status', {}).get('statusCategory', {}).get('key') == 'done')
    in_progress = sum(1 for i in all_issues if i.get('fields', {}).get('status', {}).get('statusCategory', {}).get('key') == 'indeterminate')
    to_do = total_issues - done - in_progress
    
    # Recent activity
    created_7d = 0
    updated_7d = 0
    completed_7d = 0
    
    for issue in all_issues:
        fields = issue.get('fields', {})
        try:
            created = datetime.fromisoformat(fields.get('created', '').replace('Z', '+00:00'))
            updated = datetime.fromisoformat(fields.get('updated', '').replace('Z', '+00:00'))
            status_cat = fields.get('status', {}).get('statusCategory', {}).get('key')
            
            if created >= last_7_days:
                created_7d += 1
            if updated >= last_7_days:
                updated_7d += 1
            if status_cat == 'done' and updated >= last_7_days:
                completed_7d += 1
        except:
            pass
    
    return {
        'total_projects': len(projects),
        'total_work_items': total_issues,
        'status_summary': {
            'done': done,
            'in_progress': in_progress,
            'to_do': to_do,
            'done_percentage': round((done / total_issues * 100) if total_issues > 0 else 0, 1)
        },
        'activity_last_7_days': {
            'created': created_7d,
            'updated': updated_7d,
            'completed': completed_7d
        }
    }


async def get_sprint_metrics(
    client: httpx.AsyncClient,
    base_url: str,
    projects: list
) -> dict:
    """
    Get sprint/velocity metrics (if Agile boards are enabled)
    """
    agile_base = base_url.replace('/rest/api/3', '/rest/agile/1.0')
    
    try:
        # Get all boards
        boards_url = f"{agile_base}/board"
        boards_response = await client.get(boards_url)
        boards_response.raise_for_status()
        
        boards = boards_response.json().get('values', [])
        
        sprint_data = []
        
        for board in boards[:5]:  # Limit to first 5 boards
            board_id = board.get('id')
            board_name = board.get('name')
            
            try:
                # Get active sprint
                sprints_url = f"{agile_base}/board/{board_id}/sprint?state=active"
                sprints_response = await client.get(sprints_url)
                sprints_response.raise_for_status()
                
                sprints = sprints_response.json().get('values', [])
                
                if sprints:
                    sprint = sprints[0]
                    sprint_id = sprint.get('id')
                    
                    # Get sprint issues
                    sprint_issues_url = f"{agile_base}/sprint/{sprint_id}/issue"
                    sprint_issues_response = await client.get(sprint_issues_url)
                    sprint_issues_response.raise_for_status()
                    
                    sprint_issues = sprint_issues_response.json().get('issues', [])
                    
                    sprint_data.append({
                        'board_name': board_name,
                        'sprint_name': sprint.get('name'),
                        'sprint_state': sprint.get('state'),
                        'total_issues': len(sprint_issues),
                        'start_date': sprint.get('startDate'),
                        'end_date': sprint.get('endDate')
                    })
                
                await asyncio.sleep(0.2)
            except:
                continue
        
        return {
            'active_sprints': sprint_data,
            'total_boards': len(boards)
        }
    
    except Exception as e:
        logging.warning(f"Could not fetch sprint data: {e}")
        return {}

# =================================================================
# MICROSOFT EXCEL ETL
# =================================================================

async def _run_microsoft_excel_etl(user_id: str, access_token: str) -> tuple[bool, int]:
    """
    Microsoft Excel ETL - fetches Excel files from OneDrive/SharePoint and extracts data
    Uses Microsoft Graph API to extract content without downloading files
    Returns: (success, files_count)
    """
    logging.info(f"--- Starting Microsoft Excel ETL for user: {user_id} ---")
    
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient(headers=headers, timeout=60.0) as client:
            logging.info("Fetching Excel files from OneDrive...")
            
            # Search for Excel files
            search_url = "https://graph.microsoft.com/v1.0/me/drive/root/search(q='.xlsx')"
            
            response = await client.get(search_url)
            response.raise_for_status()
            
            data = response.json()
            excel_files = data.get('value', [])
            
            logging.info(f"Found {len(excel_files)} Excel files")
            await update_sync_progress(user_id, "microsoft-excel", progress=f"0/{len(excel_files)} files")
            
            successful_count = 0
            bucket_name = "Kogna"
            
            for idx, file in enumerate(excel_files):
                file_id = file.get('id')
                file_name = file.get('name')
                file_size = file.get('size', 0)
                
                if file_size > MAX_FILE_SIZE:
                    logging.warning(f"Skipping large file: {file_name}")
                    continue
                
                try:
                    # Refresh token if needed
                    access_token = await ensure_valid_token(user_id, "microsoft-excel")
                    if not access_token:
                        raise ValueError("Token refresh failed")
                    
                    # Extract Excel content via API
                    workbook_data = await extract_excel_content_via_api(
                        client, file_id, file_name
                    )
                    
                    if workbook_data:
                        # Save extracted data as JSON
                        data_json = json.dumps(workbook_data, indent=2)
                        file_path = f"{user_id}/microsoft_excel/{file_id}_data.json"
                        
                        upload_success = await safe_upload_to_bucket(
                            bucket_name,
                            file_path,
                            data_json.encode('utf-8'),
                            "application/json",
                            enable_versioning=True
                        )
                        
                        if upload_success:
                            successful_count += 1
                            latest_path = f"{user_id}/microsoft_excel/{file_id}_data_latest.json"
                            await queue_embedding(user_id, latest_path)
                            logging.info(f"Extracted data from: {file_name}")
                    else:
                        logging.warning(f"No data extracted from: {file_name}")
                    
                    if (idx + 1) % 10 == 0:
                        await update_sync_progress(
                            user_id, "microsoft-excel",
                            progress=f"{idx+1}/{len(excel_files)} files",
                            files_processed=successful_count
                        )
                    
                    await asyncio.sleep(RATE_LIMIT_DELAY)
                
                except Exception as e:
                    logging.error(f"Error processing {file_name}: {e}")
                    continue
            
            logging.info(f"{'='*60}")
            logging.info(f"Finished Excel ETL: {successful_count}/{len(excel_files)} files")
            logging.info(f"{'='*60}")
            
            return True, successful_count
    
    except Exception as e:
        logging.error(f"Excel ETL Error: {e}")
        import traceback
        traceback.print_exc()
        return False, 0


async def extract_excel_content_via_api(
    client: httpx.AsyncClient,
    file_id: str,
    file_name: str
) -> dict:
    """
    Extract Excel content using Microsoft Graph API (no file download needed)
    Returns structured JSON with all worksheet data
    """
    try:
        # Get list of worksheets
        worksheets_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}/workbook/worksheets"
        
        worksheets_response = await client.get(worksheets_url)
        worksheets_response.raise_for_status()
        
        worksheets = worksheets_response.json().get('value', [])
        
        if not worksheets:
            logging.warning(f"No worksheets found in: {file_name}")
            return None
        
        workbook_data = {
            'file_name': file_name,
            'file_id': file_id,
            'worksheets': []
        }
        
        for worksheet in worksheets:
            sheet_name = worksheet.get('name')
            sheet_id = worksheet.get('id')
            
            try:
                # Get used range (cells with data)
                range_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}/workbook/worksheets/{sheet_id}/usedRange"
                
                range_response = await client.get(range_url)
                range_response.raise_for_status()
                
                range_data = range_response.json()
                
                # Extract cell values
                values = range_data.get('values', [])
                formulas = range_data.get('formulas', [])
                
                sheet_data = {
                    'name': sheet_name,
                    'row_count': range_data.get('rowCount', 0),
                    'column_count': range_data.get('columnCount', 0),
                    'values': values,
                    'formulas': formulas,
                    'address': range_data.get('address', '')
                }
                
                workbook_data['worksheets'].append(sheet_data)
                logging.info(f"   Extracted sheet: {sheet_name} ({sheet_data['row_count']} rows x {sheet_data['column_count']} cols)")
                
                await asyncio.sleep(0.1)  # Rate limiting between sheets
            
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    logging.warning(f"Sheet {sheet_name} is empty or inaccessible")
                else:
                    logging.error(f"Could not extract sheet {sheet_name}: {e.response.status_code}")
                continue
            except Exception as e:
                logging.warning(f"Could not extract sheet {sheet_name}: {e}")
                continue
        
        return workbook_data if workbook_data['worksheets'] else None
    
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logging.warning(f"Excel API not available for: {file_name} (might be an older format)")
        elif e.response.status_code == 403:
            logging.warning(f"Access denied to workbook: {file_name}")
        else:
            logging.error(f"API extraction error for {file_name}: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error extracting {file_name}: {e}")
        return None
# =================================================================
# MICROSOFT PROJECT ETL
# =================================================================

async def _run_microsoft_project_etl(user_id: str, access_token: str) -> tuple[bool, int]:
    """
    Microsoft Project ETL - fetches project plans and tasks from Microsoft Planner
    Note: Microsoft Planner only works with work/school accounts, not personal Microsoft accounts
    Returns: (success, files_count)
    """
    logging.info(f"--- Starting Microsoft Project ETL for user: {user_id} ---")
    
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient(headers=headers, timeout=60.0) as client:
            logging.info("Fetching Microsoft Planner plans...")
            
            all_tasks = []
            all_plans = []
            bucket_name = "Kogna"
            
            # First check account type
            try:
                me_url = "https://graph.microsoft.com/v1.0/me"
                me_response = await client.get(me_url)
                me_response.raise_for_status()
                
                me_data = me_response.json()
                user_type = me_data.get('userType')
                user_principal = me_data.get('userPrincipalName', '')
                
                logging.info(f"Account type: {user_type}, Principal: {user_principal}")
                
                # Check if this is a personal account
                if not user_principal or '@' not in user_principal:
                    logging.warning("Personal Microsoft account detected. Planner requires work/school account.")
                    
                    # Try to fetch Microsoft To Do tasks instead (available for personal accounts)
                    return await _run_microsoft_todo_fallback(user_id, access_token, client, bucket_name)
                
            except Exception as e:
                logging.warning(f"Could not determine account type: {e}")
            
            # Try to get user's planner tasks directly
            try:
                tasks_url = "https://graph.microsoft.com/v1.0/me/planner/tasks"
                
                response = await client.get(tasks_url)
                response.raise_for_status()
                
                tasks_data = response.json()
                user_tasks = tasks_data.get('value', [])
                
                logging.info(f"Found {len(user_tasks)} tasks assigned to user")
                
                # Group tasks by plan
                plans_dict = {}
                
                for task in user_tasks:
                    plan_id = task.get('planId')
                    
                    if plan_id and plan_id not in plans_dict:
                        try:
                            plan_url = f"https://graph.microsoft.com/v1.0/planner/plans/{plan_id}"
                            
                            access_token = await ensure_valid_token(user_id, "microsoft-project")
                            if not access_token:
                                raise ValueError("Token refresh failed")
                            
                            plan_response = await client.get(plan_url)
                            plan_response.raise_for_status()
                            
                            plan_data = plan_response.json()
                            plan_title = plan_data.get('title', 'Unnamed Plan')
                            
                            plans_dict[plan_id] = {
                                'id': plan_id,
                                'title': plan_title,
                                'tasks': []
                            }
                            
                            logging.info(f"   Found plan: {plan_title}")
                            await asyncio.sleep(RATE_LIMIT_DELAY)
                        
                        except httpx.HTTPStatusError as e:
                            if e.response.status_code == 403:
                                logging.warning(f"Access denied to plan: {plan_id}")
                            continue
                    
                    if plan_id in plans_dict:
                        plans_dict[plan_id]['tasks'].append(task)
                
                for plan_id, plan_data in plans_dict.items():
                    all_plans.append(plan_data)
                    
                    for task in plan_data['tasks']:
                        all_tasks.append({
                            **task,
                            'plan_title': plan_data['title'],
                            'plan_id': plan_id
                        })
                
                logging.info(f"Organized tasks into {len(plans_dict)} plans")
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 400:
                    error_data = e.response.json()
                    error_msg = error_data.get('error', {}).get('message', '')
                    
                    if 'MSA' in error_msg or 'personal' in error_msg.lower():
                        logging.warning("Personal Microsoft account detected - Planner not available")
                        logging.info("Attempting to fetch Microsoft To Do tasks instead...")
                        
                        return await _run_microsoft_todo_fallback(user_id, access_token, client, bucket_name)
                    else:
                        raise
                
                elif e.response.status_code == 403:
                    logging.error("Insufficient permissions to access Planner tasks")
                    logging.error("Required scopes: Tasks.Read, Group.Read.All")
                    return False, 0
                else:
                    raise
            
            # Try to get groups (fallback for additional plans)
            try:
                logging.info("Fetching groups for additional plans...")
                groups_url = "https://graph.microsoft.com/v1.0/me/memberOf"
                
                groups_response = await client.get(groups_url)
                groups_response.raise_for_status()
                
                all_members = groups_response.json().get('value', [])
                groups = [m for m in all_members if m.get('@odata.type') == '#microsoft.graph.group']
                
                logging.info(f"Found {len(groups)} groups")
                
                for group in groups:
                    group_id = group.get('id')
                    group_name = group.get('displayName')
                    
                    try:
                        plans_url = f"https://graph.microsoft.com/v1.0/groups/{group_id}/planner/plans"
                        
                        access_token = await ensure_valid_token(user_id, "microsoft-project")
                        if not access_token:
                            raise ValueError("Token refresh failed")
                        
                        plans_response = await client.get(plans_url)
                        plans_response.raise_for_status()
                        
                        plans = plans_response.json().get('value', [])
                        
                        for plan in plans:
                            plan_id = plan.get('id')
                            plan_title = plan.get('title')
                            
                            if plan_id in plans_dict:
                                continue
                            
                            tasks_url = f"https://graph.microsoft.com/v1.0/planner/plans/{plan_id}/tasks"
                            tasks_response = await client.get(tasks_url)
                            tasks_response.raise_for_status()
                            
                            tasks = tasks_response.json().get('value', [])
                            
                            if tasks:
                                all_tasks.extend([{
                                    **task,
                                    'group_name': group_name,
                                    'plan_title': plan_title,
                                    'plan_id': plan_id
                                } for task in tasks])
                                
                                logging.info(f"   {plan_title}: {len(tasks)} tasks")
                            
                            await asyncio.sleep(RATE_LIMIT_DELAY)
                    
                    except httpx.HTTPStatusError as e:
                        if e.response.status_code == 403:
                            logging.warning(f"No Planner access for group: {group_name}")
                        else:
                            logging.error(f"Error fetching plans from {group_name}: {e}")
                        continue
                
            except Exception as e:
                logging.warning(f"Could not fetch additional plans from groups: {e}")
            
            # Save all tasks with versioning
            if all_tasks:
                tasks_json = json.dumps(all_tasks, indent=2)
                file_path = f"{user_id}/microsoft_project/all_tasks.json"
                tasks_bytes = tasks_json.encode('utf-8')
                
                await safe_upload_to_bucket(
                    bucket_name,
                    file_path,
                    tasks_bytes,
                    "application/json",
                    enable_versioning=True
                )
                
                latest_path = f"{user_id}/microsoft_project/all_tasks_latest.json"
                await queue_embedding(user_id, latest_path)
                
                for plan in all_plans:
                    if plan['tasks']:
                        plan_json = json.dumps(plan['tasks'], indent=2)
                        plan_file_path = f"{user_id}/microsoft_project/plans/{plan['id']}_tasks.json"
                        plan_bytes = plan_json.encode('utf-8')
                        
                        await safe_upload_to_bucket(
                            bucket_name,
                            plan_file_path,
                            plan_bytes,
                            "application/json",
                            enable_versioning=True
                        )
            
            logging.info(f"{'='*60}")
            logging.info(f"Finished Project ETL: {len(all_tasks)} tasks from {len(all_plans)} plans")
            logging.info(f"{'='*60}")
            
            return True, len(all_tasks)
    
    except httpx.HTTPStatusError as e:
        logging.error(f"API Error {e.response.status_code}: {e.response.text}")
        logging.error(f"Failed URL: {e.request.url}")
        
        if e.response.status_code == 403:
            logging.error("This might be a permissions issue. Check that the app has these scopes:")
            logging.error("   - Tasks.Read or Tasks.ReadWrite")
            logging.error("   - Group.Read.All")
            logging.error("   - User.Read")
        
        return False, 0
    except Exception as e:
        logging.error(f"Project ETL Error: {e}")
        import traceback
        traceback.print_exc()
        return False, 0


async def _run_microsoft_todo_fallback(
    user_id: str, 
    access_token: str, 
    client: httpx.AsyncClient,
    bucket_name: str
) -> tuple[bool, int]:
    """
    Fallback ETL for personal Microsoft accounts - fetches Microsoft To Do tasks
    Returns: (success, files_count)
    """
    logging.info("--- Using Microsoft To Do (fallback for personal accounts) ---")
    
    try:
        # Get all task lists
        lists_url = "https://graph.microsoft.com/v1.0/me/todo/lists"
        
        lists_response = await client.get(lists_url)
        lists_response.raise_for_status()
        
        task_lists = lists_response.json().get('value', [])
        logging.info(f"Found {len(task_lists)} task lists")
        
        all_tasks = []
        
        for task_list in task_lists:
            list_id = task_list.get('id')
            list_name = task_list.get('displayName')
            
            try:
                # Get tasks for this list
                tasks_url = f"https://graph.microsoft.com/v1.0/me/todo/lists/{list_id}/tasks"
                
                # Refresh token if needed
                access_token = await ensure_valid_token(user_id, "microsoft-project")
                if not access_token:
                    raise ValueError("Token refresh failed")
                
                tasks_response = await client.get(tasks_url)
                tasks_response.raise_for_status()
                
                tasks = tasks_response.json().get('value', [])
                
                if tasks:
                    all_tasks.extend([{
                        **task,
                        'list_name': list_name,
                        'list_id': list_id
                    } for task in tasks])
                    
                    logging.info(f"   {list_name}: {len(tasks)} tasks")
                
                await asyncio.sleep(RATE_LIMIT_DELAY)
            
            except Exception as e:
                logging.error(f"Error fetching tasks from list {list_name}: {e}")
                continue
        
        # Save all tasks
        if all_tasks:
            tasks_json = json.dumps(all_tasks, indent=2)
            file_path = f"{user_id}/microsoft_todo/all_tasks.json"
            tasks_bytes = tasks_json.encode('utf-8')
            
            await safe_upload_to_bucket(
                bucket_name,
                file_path,
                tasks_bytes,
                "application/json",
                enable_versioning=True
            )
            
            latest_path = f"{user_id}/microsoft_todo/all_tasks_latest.json"
            await queue_embedding(user_id, latest_path)
            
            logging.info(f"Saved {len(all_tasks)} tasks from Microsoft To Do")
            return True, len(all_tasks)
        else:
            logging.info("No tasks found in Microsoft To Do")
            return True, 0
    
    except Exception as e:
        logging.error(f"Microsoft To Do fallback error: {e}")
        import traceback
        traceback.print_exc()
        return False, 0

# =================================================================
# ASANA ETL
# =================================================================

async def _run_asana_etl(user_id: str, access_token: str) -> tuple[bool, int]:
    """
    Asana ETL - fetches tasks and projects
    Returns: (success, files_count)
    """
    logging.info(f"--- Starting Asana ETL for user: {user_id} ---")
    
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient(headers=headers, timeout=60.0) as client:
            # Get workspaces
            logging.info(" Fetching Asana workspaces...")
            workspaces_url = "https://app.asana.com/api/1.0/workspaces"
            
            response = await client.get(workspaces_url)
            response.raise_for_status()
            
            workspaces = response.json().get('data', [])
            logging.info(f" Found {len(workspaces)} workspaces")
            
            all_tasks = []
            bucket_name = "Kogna"
            
            for workspace_idx, workspace in enumerate(workspaces):
                workspace_gid = workspace.get('gid')
                workspace_name = workspace.get('name')
                
                logging.info(f" Fetching projects from: {workspace_name}")
                
                # Get projects
                projects_url = f"https://app.asana.com/api/1.0/projects?workspace={workspace_gid}&limit=100"
                
                # Refresh token if needed
                access_token = await ensure_valid_token(user_id, "asana")
                if not access_token:
                    raise ValueError("Token refresh failed")
                
                projects_response = await client.get(projects_url)
                projects_response.raise_for_status()
                
                projects = projects_response.json().get('data', [])
                logging.info(f"    Found {len(projects)} projects")
                
                for project in projects:
                    project_gid = project.get('gid')
                    project_name = project.get('name')
                    
                    try:
                        # Get tasks for this project
                        tasks_url = f"https://app.asana.com/api/1.0/tasks?project={project_gid}&limit=100&opt_fields=name,notes,completed,due_on,assignee,created_at,modified_at"
                        
                        tasks_response = await client.get(tasks_url)
                        tasks_response.raise_for_status()
                        
                        tasks = tasks_response.json().get('data', [])
                        
                        if tasks:
                            all_tasks.extend([{
                                **task,
                                'workspace_name': workspace_name,
                                'project_name': project_name
                            } for task in tasks])
                            
                            logging.info(f"    {project_name}: {len(tasks)} tasks")
                        
                        await asyncio.sleep(RATE_LIMIT_DELAY)
                    
                    except Exception as e:
                        logging.error(f" Error fetching tasks from {project_name}: {e}")
                        continue
                
                await update_sync_progress(
                    user_id, "asana",
                    progress=f"{workspace_idx+1}/{len(workspaces)} workspaces"
                )
            
            # Save all tasks with versioning
            if all_tasks:
                tasks_json = json.dumps(all_tasks, indent=2)
                file_path = f"{user_id}/asana/all_tasks.json"
                tasks_bytes = tasks_json.encode('utf-8')
                
                await safe_upload_to_bucket(
                    bucket_name,
                    file_path,
                    tasks_bytes,
                    "application/json",
                    enable_versioning=True
                )
                
                # Queue for embedding
                latest_path = f"{user_id}/asana/all_tasks_latest.json"
                await queue_embedding(user_id, latest_path)
            
            logging.info(f"{'='*60}")
            logging.info(f" Finished Asana ETL: {len(all_tasks)} tasks")
            logging.info(f"{'='*60}")
            
            return True, len(all_tasks)
    
    except Exception as e:
        logging.error(f" Asana ETL Error: {e}")
        import traceback
        traceback.print_exc()
        return False, 0
    
    # =================================================================
# GOOGLE DRIVE ETL
# =================================================================
async def _run_google_etl(user_id: str, access_token: str) -> tuple[bool, int]:
    """
    Google Drive ETL - fetches files and extracts content from Google Drive
    Supports: Google Docs, Sheets, Slides, PDFs, and other file types
    Returns: (success, files_count)
    """
    logging.info(f"--- Starting Google Drive ETL for user: {user_id} ---")
    
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient(headers=headers, timeout=60.0) as client:
            logging.info("Fetching files from Google Drive...")
            
            # Query to get all files (excluding folders)
            # You can customize this query to filter by type, date, etc.
            query = "mimeType != 'application/vnd.google-apps.folder' and trashed = false"
            files_url = f"https://www.googleapis.com/drive/v3/files?q={quote(query)}&pageSize=100&fields=nextPageToken,files(id,name,mimeType,size,modifiedTime,createdTime,webViewLink,owners)"
            
            all_files = []
            page_token = None
            
            # Paginate through all files
            while True:
                url = files_url
                if page_token:
                    url += f"&pageToken={page_token}"
                
                # Refresh token if needed
                access_token = await ensure_valid_token(user_id, "google")
                if not access_token:
                    raise ValueError("Token refresh failed")
                
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                
                files = data.get('files', [])
                all_files.extend(files)
                
                page_token = data.get('nextPageToken')
                if not page_token:
                    break
                
                await asyncio.sleep(RATE_LIMIT_DELAY)
            
            logging.info(f"Found {len(all_files)} files")
            await update_sync_progress(user_id, "google", progress=f"0/{len(all_files)} files")
            
            successful_count = 0
            bucket_name = "Kogna"
            
            # Process each file
            for idx, file in enumerate(all_files):
                file_id = file.get('id')
                file_name = file.get('name')
                mime_type = file.get('mimeType')
                file_size = int(file.get('size', 0))
                
                # Skip very large files
                if file_size > MAX_FILE_SIZE:
                    logging.warning(f"Skipping large file: {file_name} ({file_size} bytes)")
                    continue
                
                try:
                    # Refresh token if needed
                    access_token = await ensure_valid_token(user_id, "google")
                    if not access_token:
                        raise ValueError("Token refresh failed")
                    
                    # Extract content based on file type
                    content_data = await extract_google_file_content(
                        client, file_id, file_name, mime_type, access_token
                    )
                    
                    if content_data:
                        # Save extracted content
                        file_path = f"{user_id}/google_drive/{file_id}_content.json"
                        
                        # Add metadata to content
                        full_data = {
                            'file_id': file_id,
                            'file_name': file_name,
                            'mime_type': mime_type,
                            'modified_time': file.get('modifiedTime'),
                            'created_time': file.get('createdTime'),
                            'web_link': file.get('webViewLink'),
                            'owners': file.get('owners', []),
                            'content': content_data
                        }
                        
                        data_json = json.dumps(full_data, indent=2)
                        upload_success = await safe_upload_to_bucket(
                            bucket_name,
                            file_path,
                            data_json.encode('utf-8'),
                            "application/json",
                            enable_versioning=True
                        )
                        
                        if upload_success:
                            successful_count += 1
                            latest_path = f"{user_id}/google_drive/{file_id}_content_latest.json"
                            await queue_embedding(user_id, latest_path)
                            logging.info(f"✓ Processed: {file_name}")
                    
                    # Update progress every 10 files
                    if (idx + 1) % 10 == 0:
                        await update_sync_progress(
                            user_id, "google",
                            progress=f"{idx+1}/{len(all_files)} files",
                            files_processed=successful_count
                        )
                    
                    await asyncio.sleep(RATE_LIMIT_DELAY)
                    
                except Exception as e:
                    logging.error(f"Error processing {file_name}: {e}")
                    continue
            
            logging.info(f"{'='*60}")
            logging.info(f"✓ Finished Google Drive ETL: {successful_count}/{len(all_files)} files")
            logging.info(f"{'='*60}")
            
            return True, successful_count
            
    except Exception as e:
        logging.error(f" Google Drive ETL Error: {e}")
        import traceback
        traceback.print_exc()
        return False, 0


async def extract_google_file_content(
    client: httpx.AsyncClient,
    file_id: str,
    file_name: str,
    mime_type: str,
    access_token: str
) -> dict:
    """
    Extract content from Google Drive files based on their type
    Supports Google Docs, Sheets, Slides, and downloadable files
    """
    try:
        # Google Workspace files (Docs, Sheets, Slides)
        google_export_types = {
            'application/vnd.google-apps.document': 'text/plain',  # Google Docs
            'application/vnd.google-apps.spreadsheet': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # Google Sheets
            'application/vnd.google-apps.presentation': 'text/plain',  # Google Slides
        }
        
        if mime_type in google_export_types:
            # Export Google Workspace file
            export_mime = google_export_types[mime_type]
            export_url = f"https://www.googleapis.com/drive/v3/files/{file_id}/export?mimeType={quote(export_mime)}"
            
            response = await client.get(export_url)
            response.raise_for_status()
            
            if mime_type == 'application/vnd.google-apps.document':
                # Plain text for Docs
                return {
                    'type': 'document',
                    'text': response.text
                }
            elif mime_type == 'application/vnd.google-apps.spreadsheet':
                # For Sheets, we need to parse the Excel format
                # For simplicity, we'll just note it's a spreadsheet
                return {
                    'type': 'spreadsheet',
                    'note': 'Spreadsheet content (download as Excel for full data)',
                    'size_bytes': len(response.content)
                }
            elif mime_type == 'application/vnd.google-apps.presentation':
                # Plain text for Slides
                return {
                    'type': 'presentation',
                    'text': response.text
                }
        
        # Regular files (PDFs, text files, etc.)
        elif mime_type in ['application/pdf', 'text/plain', 'text/csv']:
            # Download file content
            download_url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
            
            response = await client.get(download_url)
            response.raise_for_status()
            
            if mime_type == 'text/plain' or mime_type == 'text/csv':
                return {
                    'type': 'text_file',
                    'text': response.text
                }
            elif mime_type == 'application/pdf':
                # For PDFs, we'll store metadata (actual PDF parsing would require additional libraries)
                return {
                    'type': 'pdf',
                    'note': 'PDF file (content extraction requires PDF parser)',
                    'size_bytes': len(response.content)
                }
        
        # Other file types - just store metadata
        else:
            return {
                'type': 'other',
                'mime_type': mime_type,
                'note': f'File type: {mime_type}'
            }
    
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 403:
            logging.warning(f"Access denied to file: {file_name}")
        else:
            logging.error(f"HTTP error extracting {file_name}: {e.response.status_code}")
        return None
    except Exception as e:
        logging.error(f"Error extracting {file_name}: {e}")
        return None


# =================================================================
# MICROSOFT TEAMS ETL
# =================================================================
async def _run_microsoft_teams_etl(user_id: str, access_token: str) -> tuple[bool, int]:
    """
    Microsoft Teams ETL - fetches teams, channels, and messages
    Extracts conversations and shared files from Teams
    Returns: (success, files_count)
    """
    logging.info(f"--- Starting Microsoft Teams ETL for user: {user_id} ---")
    
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient(headers=headers, timeout=60.0) as client:
            logging.info("📱 Fetching Teams...")
            
            # Get all teams the user is a member of
            teams_url = "https://graph.microsoft.com/v1.0/me/joinedTeams"
            response = await client.get(teams_url)
            response.raise_for_status()
            teams = response.json().get('value', [])
            
            logging.info(f"Found {len(teams)} teams")
            await update_sync_progress(user_id, "microsoft-teams", progress=f"0/{len(teams)} teams")
            
            bucket_name = "Kogna"
            total_messages = 0
            total_files = 0
            
            for team_idx, team in enumerate(teams):
                team_id = team.get('id')
                team_name = team.get('displayName')
                
                logging.info(f"Processing team: {team_name}")
                
                try:
                    # Refresh token if needed
                    access_token = await ensure_valid_token(user_id, "microsoft-teams")
                    if not access_token:
                        raise ValueError("Token refresh failed")
                    
                    # Get channels for this team
                    channels_url = f"https://graph.microsoft.com/v1.0/teams/{team_id}/channels"
                    channels_response = await client.get(channels_url)
                    channels_response.raise_for_status()
                    channels = channels_response.json().get('value', [])
                    
                    logging.info(f"   Found {len(channels)} channels")
                    
                    team_data = {
                        'team_id': team_id,
                        'team_name': team_name,
                        'channels': []
                    }
                    
                    for channel in channels:
                        channel_id = channel.get('id')
                        channel_name = channel.get('displayName')
                        
                        try:
                            # Get messages from channel
                            messages_url = f"https://graph.microsoft.com/v1.0/teams/{team_id}/channels/{channel_id}/messages"
                            
                            # Refresh token if needed
                            access_token = await ensure_valid_token(user_id, "microsoft-teams")
                            if not access_token:
                                raise ValueError("Token refresh failed")
                            
                            messages_response = await client.get(messages_url)
                            messages_response.raise_for_status()
                            messages = messages_response.json().get('value', [])
                            
                            if messages:
                                channel_data = {
                                    'channel_id': channel_id,
                                    'channel_name': channel_name,
                                    'message_count': len(messages),
                                    'messages': messages
                                }
                                
                                team_data['channels'].append(channel_data)
                                total_messages += len(messages)
                                
                                logging.info(f"      {channel_name}: {len(messages)} messages")
                            
                            # Get files shared in channel (if any)
                            try:
                                files_url = f"https://graph.microsoft.com/v1.0/teams/{team_id}/channels/{channel_id}/filesFolder"
                                files_response = await client.get(files_url)
                                
                                if files_response.status_code == 200:
                                    files_folder = files_response.json()
                                    
                                    # Get children (files) in the folder
                                    folder_id = files_folder.get('id')
                                    if folder_id:
                                        children_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{folder_id}/children"
                                        children_response = await client.get(children_url)
                                        
                                        if children_response.status_code == 200:
                                            files = children_response.json().get('value', [])
                                            if files:
                                                total_files += len(files)
                                                # Add files to channel data
                                                if 'files' not in channel_data:
                                                    channel_data['files'] = []
                                                channel_data['files'] = files
                                                logging.info(f"      📎 {len(files)} files")
                            except Exception as e:
                                logging.debug(f"Could not fetch files for {channel_name}: {e}")
                            
                            await asyncio.sleep(RATE_LIMIT_DELAY)
                            
                        except httpx.HTTPStatusError as e:
                            if e.response.status_code == 403:
                                logging.warning(f"     Access denied to channel: {channel_name}")
                            else:
                                logging.error(f"Error fetching messages from {channel_name}: {e}")
                            continue
                    
                    # Save team data with versioning
                    if team_data['channels']:
                        team_json = json.dumps(team_data, indent=2)
                        file_path = f"{user_id}/microsoft_teams/{team_id}_data.json"
                        
                        await safe_upload_to_bucket(
                            bucket_name,
                            file_path,
                            team_json.encode('utf-8'),
                            "application/json",
                            enable_versioning=True
                        )
                        
                        latest_path = f"{user_id}/microsoft_teams/{team_id}_data_latest.json"
                        await queue_embedding(user_id, latest_path)
                    
                    await update_sync_progress(
                        user_id, "microsoft-teams",
                        progress=f"{team_idx+1}/{len(teams)} teams",
                        files_processed=total_messages
                    )
                    
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 403:
                        logging.warning(f"  Access denied to team: {team_name}")
                    else:
                        logging.error(f"Error processing team {team_name}: {e}")
                    continue
            
            # Create summary
            summary = {
                'total_teams': len(teams),
                'total_messages': total_messages,
                'total_files': total_files,
                'extracted_at': int(time.time())
            }
            
            summary_json = json.dumps(summary, indent=2)
            summary_path = f"{user_id}/microsoft_teams/summary.json"
            await safe_upload_to_bucket(
                bucket_name,
                summary_path,
                summary_json.encode('utf-8'),
                "application/json",
                enable_versioning=True
            )
            
            logging.info(f"{'='*60}")
            logging.info(f"✓ Finished Teams ETL: {total_messages} messages, {total_files} files from {len(teams)} teams")
            logging.info(f"{'='*60}")
            
            return True, total_messages
            
    except httpx.HTTPStatusError as e:
        logging.error(f" API Error {e.response.status_code}: {e.response.text}")
        logging.error(f"Failed URL: {e.request.url}")
        
        if e.response.status_code == 403:
            logging.error("  Permission error. Required scopes:")
            logging.error("   - Team.ReadBasic.All")
            logging.error("   - Channel.ReadBasic.All")
            logging.error("   - ChannelMessage.Read.All")
            logging.error("   - Files.Read.All")
        
        return False, 0
        
    except Exception as e:
        logging.error(f" Teams ETL Error: {e}")
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
