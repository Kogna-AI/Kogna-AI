"""
🔥 BASE ETL UTILITIES - SHARED ACROSS ALL ETL MODULES

This module contains all shared functionality used by ETL pipelines:
- Token management (refresh logic)
- File upload helpers
- Progress tracking
- Embedding queue management

All ETL modules import from this to avoid code duplication.
"""

import os
import time
import asyncio
import httpx
import logging
import hashlib
from typing import Optional, Dict, List
from collections import deque

from supabase_connect import get_supabase_manager

supabase = get_supabase_manager().client
logging.basicConfig(level=logging.INFO)


# =================================================================
# CONSTANTS
# =================================================================

MAX_FILE_SIZE = 50_000_000  # 50MB max file size
RATE_LIMIT_DELAY = 0.1  # 100ms between requests
TOKEN_REFRESH_BUFFER = 300  # Refresh if expiring within 5 minutes


# =================================================================
# EMBEDDING QUEUE (GLOBAL)
# =================================================================

embedding_queue = deque()


def queue_embedding(user_id: str, file_path: str):
    """Add file to embedding queue"""
    embedding_queue.append({'user_id': user_id, 'file_path': file_path})
    logging.info(f" Queued for embedding: {file_path}")


async def process_embedding_queue_batch():
    """Process all items in embedding queue"""
    from services.embedding_service import embed_and_store_file
    
    logging.info(f" Processing {len(embedding_queue)} embeddings...")
    
    processed = 0
    failed = 0
    
    while embedding_queue:
        item = embedding_queue.popleft()
        user_id = item['user_id']
        file_path = item['file_path']
        
        try:
            await embed_and_store_file(user_id, file_path)
            processed += 1
            logging.info(f" Embedded ({processed}): {file_path}")
        except Exception as e:
            failed += 1
            logging.error(f" Failed embedding: {file_path} - {e}")
        
        await asyncio.sleep(0.1)
    
    logging.info(f" Embedding complete: {processed} succeeded, {failed} failed")


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
        logging.error(f" Failed to create sync job: {e}")
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
        logging.error(f" Failed to update sync progress: {e}")


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
        logging.error(f" Failed to complete sync job: {e}")


# =================================================================
# TOKEN MANAGEMENT
# =================================================================

async def ensure_valid_token(user_id: str, service: str) -> Optional[str]:
    """
    Gets a valid token, refreshing if necessary.
    Checks if token is expiring within 5 minutes.
    
    Args:
        user_id: User ID
        service: Service name (google, jira, microsoft-excel, etc.)
        
    Returns:
        Valid access token or None
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
            logging.error(f" No connector found for {service}")
            return None

        expires_at = int(data.get("expires_at", 0))
        current_time = int(time.time())
        
        # Refresh if expiring within buffer time
        if current_time + TOKEN_REFRESH_BUFFER > expires_at:
            logging.info(f" Token expiring soon for {service}. Refreshing...")
            refresh_token = data.get("refresh_token")
            
            if not refresh_token:
                logging.error(" No refresh token available")
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
                logging.error(f" Failed to refresh token for {service}")
                return None

        return data["access_token"]
        
    except Exception as e:
        logging.error(f" Error ensuring valid token: {e}")
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
        logging.error(f" Error refreshing Jira token: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        logging.error(f" Unexpected error refreshing Jira token: {e}")
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
        logging.error(f" Error refreshing Google token: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        logging.error(f" Unexpected error refreshing Google token: {e}")
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
        logging.error(f" Error refreshing Microsoft token: {e}")
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
        logging.error(f" Error refreshing Asana token: {e}")
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
    
    Args:
        bucket_name: Supabase bucket name
        file_path: Target file path in bucket
        content: File content as bytes
        mime_type: MIME type
        enable_versioning: Enable versioning (default True)
        
    Returns:
        bool: Success status
    """
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
            logging.debug(f" Uploading versioned file: {versioned_path}")
            version_response = supabase.storage.from_(bucket_name).upload(
                path=versioned_path,
                file=content,
                file_options={"content-type": mime_type}
            )
            
            if hasattr(version_response, 'error') and version_response.error:
                logging.error(f" Versioned upload failed: {version_response.error}")
                return False
            
            # Update latest pointer (with upsert)
            logging.debug(f" Updating latest pointer: {latest_path}")
            latest_response = supabase.storage.from_(bucket_name).upload(
                path=latest_path,
                file=content,
                file_options={"content-type": mime_type, "upsert": "true"}
            )
            
            if hasattr(latest_response, 'error') and latest_response.error:
                logging.warning(f" Latest pointer update failed, but version saved")
            
            logging.debug(f" Uploaded: {versioned_path} (hash: {content_hash})")
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
            
            logging.debug(f" Uploaded: {file_path}")
            return True
        
    except Exception as e:
        error_str = str(e).lower()
        
        if "already exists" in error_str or "duplicate" in error_str:
            try:
                logging.info(f" File exists, updating: {file_path}")
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
# EXPORTS
# =================================================================

__all__ = [
    # Constants
    'MAX_FILE_SIZE',
    'RATE_LIMIT_DELAY',
    'TOKEN_REFRESH_BUFFER',
    
    # Embedding queue
    'embedding_queue',
    'queue_embedding',
    'process_embedding_queue_batch',
    
    # Progress tracking
    'create_sync_job',
    'update_sync_progress',
    'complete_sync_job',
    
    # Token management
    'ensure_valid_token',
    'refresh_jira_token',
    'refresh_google_token',
    'refresh_microsoft_token',
    'refresh_asana_token',
    
    # File upload
    'safe_upload_to_bucket',
]