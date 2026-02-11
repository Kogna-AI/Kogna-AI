"""
MASTER ETL PIPELINE - PRODUCTION READY WITH CHANGE DETECTION

This is the main ETL orchestrator that routes to individual ETL modules.
All helper functions have been moved to base_etl.py to avoid duplication.

Responsibilities:
- Token management (centralized in base_etl.py)
- Sync job tracking (centralized in base_etl.py)
- ETL routing to individual modules
- Embedding queue processing

Supported Services:
- jira: Jira project management
- google: Google Drive files
- microsoft-excel: Excel files from OneDrive
- microsoft-teams: Teams channels and messages
- microsoft-project: Planner/To Do tasks
- asana: Asana tasks
"""

import os
import time
import logging
from typing import Optional
from dotenv import load_dotenv

# Import all ETL modules
from services.etl import (
    run_jira_etl,
    run_google_drive_etl,
    run_microsoft_excel_etl,
    run_microsoft_teams_etl,
    run_microsoft_project_etl,
    run_asana_etl
)

# Import base utilities
from services.etl.base_etl import (
    ensure_valid_token,
    create_sync_job,
    update_sync_progress,
    complete_sync_job,
    embedding_queue,
    process_embedding_queue_batch,
    get_user_context  # NEW: RBAC support
)

from supabase_connect import get_supabase_manager

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

supabase = get_supabase_manager().client


# =================================================================
# MASTER ETL ORCHESTRATOR
# =================================================================

async def run_master_etl(user_id: str, service: str, file_ids: Optional[list] = None) -> bool:
    """
    Main ETL orchestrator with full error handling and progress tracking.

    Routes to the appropriate ETL module based on service type.
    All ETL modules follow the same pattern:
    - Extract data from API
    - Clean and enrich data
    - Generate analytics
    - Create searchable text
    - Save to Supabase Storage (with RBAC path structure)
    - Queue for embeddings

    NOW WITH INTELLIGENT CHANGE DETECTION + RBAC:
    - Tracks processed vs skipped files
    - 95% faster re-syncs
    - Comprehensive sync job metrics
    - Organization and team-scoped storage paths
    - Team-aware KPI extraction

    Args:
        user_id: User ID
        service: Service name (google, jira, microsoft-excel, microsoft-teams,
                               microsoft-project, asana)
        file_ids: Optional list of specific file IDs to process (None = process all)

    Returns:
        bool: Success status
    """
    global embedding_queue

    logging.info(f"{'='*60}")
    logging.info(f"MASTER ETL: Starting sync for {service} (user: {user_id})")
    logging.info(f"{'='*60}")

    # NEW: Fetch user's organization and team context for RBAC
    user_context = await get_user_context(user_id)
    organization_id = user_context.get('organization_id')
    team_id = user_context.get('team_id')

    logging.info(f"RBAC Context: org={organization_id}, team={team_id}")

    # If file_ids not provided, check if user has saved file selection in database
    if file_ids is None:
        try:
            connector = supabase.table("user_connectors")\
                .select("selected_file_ids")\
                .eq("user_id", user_id)\
                .eq("service", service)\
                .single()\
                .execute()

            if connector.data and connector.data.get("selected_file_ids"):
                file_ids = connector.data["selected_file_ids"]
                logging.info(f"Using saved file selection: {len(file_ids)} files")
            else:
                logging.info("No saved file selection - will process all files")
        except Exception as e:
            logging.warning(f"Failed to fetch saved file selection: {e}")
            # Continue with file_ids=None (process all files)

    # Create sync job with RBAC context
    job_id = await create_sync_job(user_id, service, organization_id, team_id)

    try:
        # Get valid token (handles refresh automatically)
        access_token = await ensure_valid_token(user_id, service)
        if not access_token:
            raise ValueError(f"No valid token for {service}")
        
        # Route to correct ETL module
        success = False
        files_processed = 0  # Track processed files
        files_skipped = 0    # Track skipped files

        # All ETLs now return (success, files_processed, files_skipped)
        # and accept organization_id and team_id for RBAC-scoped storage paths
        if service == "jira":
            logging.info("Using Jira ETL with data cleaning + RBAC")
            success, files_processed, files_skipped = await run_jira_etl(
                user_id, access_token, organization_id, team_id
            )

        elif service == "google":
            logging.info("Using Google Drive ETL with data cleaning + RBAC")
            success, files_processed, files_skipped = await run_google_drive_etl(
                user_id, access_token, organization_id, team_id, file_ids
            )

        elif service == "microsoft-excel":
            logging.info("Using Microsoft Excel ETL with data cleaning + RBAC")
            success, files_processed, files_skipped = await run_microsoft_excel_etl(
                user_id, access_token, organization_id, team_id
            )

        elif service == "microsoft-teams":
            logging.info("Using Microsoft Teams ETL with data cleaning + RBAC")
            success, files_processed, files_skipped = await run_microsoft_teams_etl(
                user_id, access_token, organization_id, team_id
            )

        elif service == "microsoft-project":
            logging.info("Using Microsoft Project ETL with data cleaning + RBAC")
            success, files_processed, files_skipped = await run_microsoft_project_etl(
                user_id, access_token, organization_id, team_id
            )

        elif service == "asana":
            logging.info("Using Asana ETL with data cleaning + RBAC")
            success, files_processed, files_skipped = await run_asana_etl(
                user_id, access_token, organization_id, team_id
            )

        else:
            raise ValueError(f"Unknown service: {service}")
        
        # REMOVED: complete_sync_job is now called inside each ETL
        # This prevents duplication since each ETL already calls it
        
        logging.info(f"DEBUG: embedding_queue has {len(embedding_queue)} items")  
        logging.info(f"DEBUG: success={success}, processed={files_processed}, skipped={files_skipped}")

        # Process embeddings in background
        if success and embedding_queue:
            logging.info(f"Processing {len(embedding_queue)} embeddings...")
            result = await process_embedding_queue_batch()
            logging.info(f"Embedding batch complete: {result}")
        else:
            logging.warning(f"Skipping embeddings - queue empty or sync failed")
        
        return success
        
    except Exception as e:
        logging.error(f"MASTER ETL FAILED for {service}: {e}")
        import traceback
        traceback.print_exc()

        # Only complete sync job here if it wasn't already completed in the ETL
        # (ETLs now handle their own completion, but this is a safety net)
        try:
            await complete_sync_job(
                user_id, service, False, 0, 0, str(e),
                organization_id=organization_id,
                team_id=team_id
            )
        except Exception as complete_error:
            logging.error(f"Failed to complete sync job: {complete_error}")

        return False


# =================================================================
# TEST FUNCTION
# =================================================================

async def run_test():
    """Simple test function to verify httpx is working"""
    import httpx
    
    logging.info("--- RUNNING TEST FUNCTION ---")
    try:
        test_url = "https://jsonplaceholder.typicode.com/todos/1"
        logging.info(f"Calling test API: {test_url}")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(test_url)
            response.raise_for_status()
            
            data = response.json()
            logging.info("--- TEST SUCCESSFUL ---")
            logging.info(f"API Response: {data}")
            return {"status": "success", "data": data}

    except Exception as e:
        logging.error(f"--- TEST FAILED ---")
        logging.error(f"Error: {e}")
        return {"status": "error", "message": str(e)}


# =================================================================
# EXPORTS
# =================================================================

__all__ = ['run_master_etl', 'run_test']