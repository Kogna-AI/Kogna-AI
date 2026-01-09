"""
🔥 ETL Module - Data Extraction, Transformation, and Loading

This module provides ETL functionality for multiple data sources:
- Jira: Project management and issue tracking
- Google Drive: Files and documents
- Microsoft Excel: Spreadsheets from OneDrive
- Microsoft Teams: Team channels and messages
- Microsoft Project: Planner tasks and To Do lists
- Asana: Task management

All ETL modules follow the same pattern:
1. Extract data from API
2. Clean and enrich data
3. Generate analytics
4. Create searchable text
5. Save to Supabase Storage
6. Queue for embeddings

Usage:
    from services.etl import run_jira_etl, run_google_drive_etl
    
    success, count = await run_jira_etl(user_id, access_token)
"""

# Import all ETL functions
from .google_drive_etl import run_google_drive_etl
from .jira_etl import run_jira_etl
from .microsoft_excel_etl import run_microsoft_excel_etl
from .microsoft_teams_etl import run_microsoft_teams_etl
from .microsoft_project_etl import run_microsoft_project_etl
from .asana_etl import run_asana_etl

# Import base utilities (optional - for advanced usage)
from .base_etl import (
    MAX_FILE_SIZE,
    RATE_LIMIT_DELAY,
    TOKEN_REFRESH_BUFFER,
    safe_upload_to_bucket,
    ensure_valid_token,
    queue_embedding,
    process_embedding_queue_batch,
)

# Public API
__all__ = [
    # ETL Functions
    'run_google_drive_etl',
    'run_jira_etl',
    'run_microsoft_excel_etl',
    'run_microsoft_teams_etl',
    'run_microsoft_project_etl',
    'run_asana_etl',
    
    # Base Utilities (for advanced usage)
    'MAX_FILE_SIZE',
    'RATE_LIMIT_DELAY',
    'TOKEN_REFRESH_BUFFER',
    'safe_upload_to_bucket',
    'ensure_valid_token',
    'queue_embedding',
    'process_embedding_queue_batch',
]

# Version
__version__ = '1.0.0'