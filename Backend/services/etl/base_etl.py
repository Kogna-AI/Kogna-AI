"""
BASE ETL UTILITIES - SHARED ACROSS ALL ETL MODULES

This module contains all shared functionality used by ETL pipelines:
- Token management (refresh logic)
- File upload helpers (with intelligent change detection)
- Progress tracking
- Embedding queue management

All ETL modules import from this to avoid code duplication.

CRITICAL DESIGN:
- Files are UPLOADED immediately
- Files are QUEUED for processing (not processed immediately)
- Processing happens in BATCH at the end (via process_embedding_queue_batch)
- This ensures proper note generation after all embeddings are done
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


def queue_embedding(user_id: str, file_path: str, source_type: str = "upload", source_id: Optional[str] = None, source_metadata: Optional[Dict] = None):
    """
    Add file to embedding queue.
    
    Args:
        user_id: User ID
        file_path: Path in storage bucket
        source_type: 'google_drive', 'jira', 'asana', 'upload', etc.
        source_id: External ID (optional)
        source_metadata: Connector-specific metadata (optional)
    """
    embedding_queue.append({
        'user_id': user_id, 
        'file_path': file_path,
        'source_type': source_type,
        'source_id': source_id,
        'source_metadata': source_metadata
    })
    logging.info(f"Queued for embedding: {file_path}")


async def process_embedding_queue_batch():
    """
    Process all items in embedding queue with change detection.
    
    This is where the actual embedding and note generation happens.
    Call this AFTER all files have been uploaded and queued.
    
    Returns:
        Dict with processed, skipped, and failed counts
    """
    from services.embedding_service import embed_and_store_file
    
    logging.info(f"Processing {len(embedding_queue)} embeddings...")
    
    processed = 0
    skipped = 0
    failed = 0
    
    while embedding_queue:
        item = embedding_queue.popleft()
        user_id = item['user_id']
        file_path = item['file_path']
        source_type = item.get('source_type', 'upload')
        source_id = item.get('source_id')
        source_metadata = item.get('source_metadata')
        
        try:
            result = await embed_and_store_file(
                user_id=user_id,
                file_path_in_bucket=file_path,
                source_type=source_type,
                source_id=source_id,
                source_metadata=source_metadata
            )
            
            if result['status'] == 'skipped':
                skipped += 1
                logging.info(f"Skipped ({skipped}): {file_path}")
            elif result['status'] == 'success':
                processed += 1
                logging.info(f"Embedded ({processed}): {file_path}")
            else:
                failed += 1
                logging.error(f"Failed ({failed}): {file_path}")
                
        except Exception as e:
            failed += 1
            logging.error(f"Failed embedding: {file_path} - {e}")
        
        await asyncio.sleep(0.1)
    
    logging.info(f"Embedding complete: {processed} processed, {skipped} skipped, {failed} failed")
    
    return {
        'processed': processed,
        'skipped': skipped,
        'failed': failed
    }


# =================================================================
# SMART UPLOAD AND QUEUE (CORRECT NAME!)
# =================================================================

async def smart_upload_and_embed(
    user_id: str,
    bucket_name: str,
    file_path: str,
    content: bytes,
    mime_type: str,
    source_type: str,
    source_id: Optional[str] = None,
    source_metadata: Optional[Dict] = None,
    enable_versioning: bool = False,
    process_content_directly: bool = True  # Kept for API compatibility
) -> Dict:
    """
    UPLOADS file and QUEUES for batch processing.
    
    IMPORTANT: This does NOT process files immediately!
    - Uploads file to storage
    - Queues file for batch processing
    - Returns 'queued' status
    
    Actual processing (embedding + note generation) happens later
    when process_embedding_queue_batch() is called.
    
    Workflow:
    1. Upload to Supabase Storage
    2. Queue for batch processing
    3. Return 'queued' status
    
    Later (in etl_pipelines.py):
    4. process_embedding_queue_batch() runs
    5. All files processed with change detection
    6. Notes generated for ALL files together
    
    Args:
        user_id: User ID
        bucket_name: Storage bucket (usually "Kogna")
        file_path: Path in bucket (e.g., "user123/google_drive/report.pdf")
        content: File content as bytes
        mime_type: MIME type (e.g., "application/pdf")
        source_type: 'google_drive', 'jira', 'asana', 'upload', etc.
        source_id: External ID (e.g., Google Drive file ID, Jira issue key)
        source_metadata: Connector-specific metadata (modified_time, etc.)
        enable_versioning: If True, keeps timestamped versions
        process_content_directly: Kept for API compatibility (not used)
    
    Returns:
        {
            'status': 'queued',  # Always queued, never 'success' immediately
            'message': 'File uploaded and queued for processing',
            'storage_path': str
        }
    
    Example usage:
        result = await smart_upload_and_embed(
            user_id=user_id,
            bucket_name="Kogna",
            file_path=f"{user_id}/jira/{issue_key}.json",
            content=json_content.encode('utf-8'),
            mime_type="application/json",
            source_type="jira",
            source_id=issue_key
        )
        
        if result['status'] == 'queued':
            files_queued += 1  # Count as queued, will process in batch
    """
    
    try:
        # =====================================================================
        # STEP 1: UPLOAD TO STORAGE
        # =====================================================================
        
        logging.info(f"Uploading: {file_path}")
        
        # Upload file to storage
        try:
            upload_result = supabase.storage.from_(bucket_name).upload(
                path=file_path,
                file=content,
                file_options={
                    "content-type": mime_type,
                    "upsert": "true"  # FIXED: String instead of boolean
                }
            )
            
            logging.info(f"Uploaded to storage: {file_path}")
            
        except Exception as upload_error:
            logging.error(f"Upload failed: {upload_error}")
            return {
                'status': 'error',
                'message': f'Upload failed: {str(upload_error)}',
                'storage_path': file_path
            }
        
        # Optional: Store versioned copy
        if enable_versioning:
            try:
                timestamp = int(time.time())
                version_path = f"{file_path}_v{timestamp}"
                
                supabase.storage.from_(bucket_name).upload(
                    path=version_path,
                    file=content,
                    file_options={
                        "content-type": mime_type,
                        "upsert": "true"  # FIXED: String instead of boolean
                    }
                )
                
                logging.info(f"Versioned copy: {version_path}")
                
            except Exception as version_error:
                # Non-critical, just log
                logging.warning(f"Versioning failed (non-critical): {version_error}")
        
        # =====================================================================
        # STEP 2: QUEUE FOR BATCH PROCESSING (DON'T PROCESS NOW!)
        # =====================================================================
        
        queue_embedding(
            user_id=user_id,
            file_path=file_path,
            source_type=source_type,
            source_id=source_id,
            source_metadata=source_metadata
        )
        
        # Return queued status (processing happens later in batch)
        return {
            'status': 'queued',  # NOT 'success' - will be processed later
            'message': 'File uploaded and queued for processing',
            'storage_path': file_path
        }
        
    except Exception as e:
        logging.error(f"Error in smart_upload_and_embed: {e}")
        return {
            'status': 'error',
            'message': f'Error: {str(e)}',
            'storage_path': file_path
        }


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
            "files_processed": 0,
            "files_skipped": 0  # Track skipped files
        }).execute()
        
        if response.data:
            job_id = response.data[0]['id']
            logging.info(f"Created sync job {job_id} for {service}")
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


async def complete_sync_job(
    user_id: str, 
    service: str, 
    success: bool, 
    files_count: int = 0,
    skipped_count: int = 0,  # NEW: Track skipped files
    error: str = None
):
    """
    Marks sync job as completed or failed.
    
    Args:
        user_id: User ID
        service: Service name
        success: Whether sync succeeded
        files_count: Number of files processed (new/modified only)
        skipped_count: Number of files skipped (unchanged)
        error: Error message if failed
    """
    try:
        updates = {
            "status": "completed" if success else "failed",
            "finished_at": int(time.time()),
            "files_processed": files_count,
            "files_skipped": skipped_count,  # NEW
            "total_files": files_count + skipped_count  # NEW
        }
        if error:
            updates["error_message"] = str(error)[:500]
        
        supabase.table("sync_jobs") \
            .update(updates) \
            .eq("user_id", user_id) \
            .eq("service", service) \
            .eq("status", "running") \
            .execute()
        
        status = "COMPLETED" if success else "FAILED"
        logging.info(f"{status} sync job for {service}")
        logging.info(f"   Processed: {files_count}, Skipped: {skipped_count}, Total: {files_count + skipped_count}")
    except Exception as e:
        logging.error(f"Failed to complete sync job: {e}")


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
            logging.error(f"No connector found for {service}")
            return None

        expires_at = int(data.get("expires_at", 0))
        current_time = int(time.time())
        
        # Refresh if expiring within buffer time
        if current_time + TOKEN_REFRESH_BUFFER > expires_at:
            logging.info(f"Token expiring soon for {service}. Refreshing...")
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
                
                logging.info("Token refreshed successfully")
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
# LEGACY FILE UPLOAD (BACKWARD COMPATIBILITY)
# =================================================================

async def safe_upload_to_bucket(
    bucket_name: str, 
    file_path: str, 
    content: bytes, 
    mime_type: str,
    enable_versioning: bool = False
) -> bool:
    """
    LEGACY FUNCTION - For backward compatibility only
    
    NEW CODE SHOULD USE: smart_upload_and_embed()
    
    This is a simple upload without change detection or embedding.
    """
    try:
        upload_response = supabase.storage.from_(bucket_name).upload(
            path=file_path,
            file=content,
            file_options={
                "content-type": mime_type,
                "upsert": "true"  # FIXED: String instead of boolean
            }
        )
        
        if hasattr(upload_response, 'error') and upload_response.error:
            logging.error(f"Upload failed: {upload_response.error}")
            return False
        
        logging.info(f"Uploaded: {file_path}")
        return True
        
    except Exception as e:
        logging.error(f"Error uploading {file_path}: {e}")
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
    
    # Smart upload (uploads + queues, does NOT process immediately)
    'smart_upload_and_embed',
    
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
    
    # Legacy file upload (backward compatibility)
    'safe_upload_to_bucket',
]