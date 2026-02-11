#!/usr/bin/env python3
"""
Migrate storage paths from legacy format to RBAC-scoped format.

This script helps migrate files in Supabase Storage from the old path structure
to the new RBAC-scoped path structure.

Old path format: {user_id}/{connector_type}/{filename}
New path format: {organization_id}/{team_id}/{connector_type}/{user_id}/{filename}

This is a "lazy migration" approach:
- New syncs already use new paths (implemented in ETL modules)
- This script can be run to migrate old files to new paths
- Old files remain accessible at original paths until migrated

Usage:
    # Dry run (default) - shows what would be migrated
    python Backend/scripts/migrate_storage_paths.py

    # Execute the migration
    python Backend/scripts/migrate_storage_paths.py --execute

    # Migrate specific connector types only
    python Backend/scripts/migrate_storage_paths.py --execute --connectors google_drive,jira

    # Migrate for specific user
    python Backend/scripts/migrate_storage_paths.py --execute --user-id <USER_UUID>

    # Verbose output
    python Backend/scripts/migrate_storage_paths.py --execute --verbose
"""

import os
import sys
import argparse
import logging
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# Add Backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv()

from supabase_connect import get_supabase_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Connector types to migrate
CONNECTOR_TYPES = [
    "google_drive",
    "jira",
    "asana",
    "microsoft_excel",
    "microsoft_teams",
    "microsoft_project",
]

# Storage bucket name
BUCKET_NAME = "Kogna"


def get_supabase_client():
    """Get Supabase client instance."""
    return get_supabase_manager().client


def get_user_context(supabase, user_id: str) -> Optional[Dict]:
    """
    Get user's organization_id and primary team_id.

    Args:
        supabase: Supabase client
        user_id: User ID

    Returns:
        Dict with organization_id and team_id, or None if user not found
    """
    try:
        # Get organization_id from users table
        user_response = supabase.table("users") \
            .select("organization_id") \
            .eq("id", user_id) \
            .maybe_single() \
            .execute()

        user_data = user_response.data
        if not user_data:
            return None

        organization_id = user_data.get("organization_id")

        # Get primary team_id from team_members table
        team_response = supabase.table("team_members") \
            .select("team_id") \
            .eq("user_id", user_id) \
            .eq("is_primary", True) \
            .maybe_single() \
            .execute()

        team_data = team_response.data
        team_id = team_data.get("team_id") if team_data else None

        return {
            "organization_id": organization_id,
            "team_id": team_id
        }

    except Exception as e:
        logger.error(f"Error fetching user context for {user_id}: {e}")
        return None


def parse_legacy_path(file_path: str) -> Optional[Dict]:
    """
    Parse a legacy storage path to extract components.

    Legacy format: {user_id}/{connector_type}/{filename}
    Or: {user_id}/{connector_type}/subdir/{filename}

    Args:
        file_path: Storage path

    Returns:
        Dict with user_id, connector_type, filename or None if not legacy format
    """
    # Skip paths that already look like RBAC paths
    # RBAC paths have: {org_id}/{team_id or "no-team"}/{connector_type}/{user_id}/{filename}
    parts = file_path.split("/")

    if len(parts) < 3:
        return None

    # Check if first part looks like a UUID (user_id in legacy format)
    uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)

    # In legacy format, first part is user_id
    potential_user_id = parts[0]
    if not uuid_pattern.match(potential_user_id):
        return None

    # Second part should be connector_type
    connector_type = parts[1]
    if connector_type not in CONNECTOR_TYPES:
        # Could be a different folder structure, skip
        return None

    # Rest is the filename (could include subdirectories)
    filename = "/".join(parts[2:])

    return {
        "user_id": potential_user_id,
        "connector_type": connector_type,
        "filename": filename,
        "original_path": file_path
    }


def build_new_path(
    user_id: str,
    connector_type: str,
    filename: str,
    organization_id: str,
    team_id: Optional[str]
) -> str:
    """
    Build the new RBAC-scoped storage path.

    Args:
        user_id: User ID
        connector_type: Connector type (google_drive, jira, etc.)
        filename: Original filename (may include subdirectories)
        organization_id: Organization ID
        team_id: Team ID (None = "no-team")

    Returns:
        New path: {org_id}/{team_id}/{connector_type}/{user_id}/{filename}
    """
    team_folder = team_id if team_id else "no-team"
    return f"{organization_id}/{team_folder}/{connector_type}/{user_id}/{filename}"


def list_legacy_files(supabase, connector_types: List[str], user_id: Optional[str] = None) -> List[Dict]:
    """
    List files that need to be migrated from legacy paths.

    Args:
        supabase: Supabase client
        connector_types: List of connector types to check
        user_id: Optional specific user ID to filter

    Returns:
        List of file info dicts with parsed path components
    """
    files_to_migrate = []

    try:
        # List all files in bucket
        # Note: Supabase storage list() returns files in the specified path
        # We need to list at the root level to find legacy paths

        # Get all users if not filtering by specific user
        if user_id:
            users = [{"id": user_id}]
        else:
            users_response = supabase.table("users").select("id").execute()
            users = users_response.data or []

        for user_data in users:
            uid = user_data["id"]

            for connector in connector_types:
                legacy_prefix = f"{uid}/{connector}"

                try:
                    # List files in the legacy path
                    files = supabase.storage.from_(BUCKET_NAME).list(legacy_prefix)

                    for file_info in files or []:
                        file_name = file_info.get("name")
                        if file_name:
                            full_path = f"{legacy_prefix}/{file_name}"
                            parsed = parse_legacy_path(full_path)
                            if parsed:
                                parsed["file_info"] = file_info
                                files_to_migrate.append(parsed)

                except Exception as e:
                    # Path may not exist, that's OK
                    if "not found" not in str(e).lower():
                        logger.debug(f"Error listing {legacy_prefix}: {e}")

    except Exception as e:
        logger.error(f"Error listing files: {e}")

    return files_to_migrate


def migrate_file(
    supabase,
    file_data: Dict,
    user_context: Dict,
    dry_run: bool = True,
    verbose: bool = False
) -> Tuple[bool, str]:
    """
    Migrate a single file from legacy path to RBAC path.

    Args:
        supabase: Supabase client
        file_data: Parsed file data from parse_legacy_path
        user_context: User's org_id and team_id
        dry_run: If True, don't actually migrate
        verbose: If True, log details

    Returns:
        Tuple of (success, message)
    """
    old_path = file_data["original_path"]
    new_path = build_new_path(
        user_id=file_data["user_id"],
        connector_type=file_data["connector_type"],
        filename=file_data["filename"],
        organization_id=user_context["organization_id"],
        team_id=user_context.get("team_id")
    )

    if dry_run:
        if verbose:
            logger.info(f"  [DRY RUN] Would migrate:")
            logger.info(f"    FROM: {old_path}")
            logger.info(f"    TO:   {new_path}")
        return True, "dry_run"

    try:
        # Download the file
        content = supabase.storage.from_(BUCKET_NAME).download(old_path)

        if not content:
            return False, "download_failed"

        # Upload to new path
        supabase.storage.from_(BUCKET_NAME).upload(
            path=new_path,
            file=content,
            file_options={
                "content-type": "application/octet-stream",
                "upsert": "true"
            }
        )

        if verbose:
            logger.info(f"  Migrated: {old_path} -> {new_path}")

        return True, "migrated"

    except Exception as e:
        logger.error(f"  Failed to migrate {old_path}: {e}")
        return False, str(e)


def run_migration(
    connector_types: Optional[List[str]] = None,
    user_id: Optional[str] = None,
    dry_run: bool = True,
    verbose: bool = False,
    delete_old: bool = False
) -> Dict[str, Dict[str, int]]:
    """
    Run the storage migration process.

    Args:
        connector_types: List of connector types to migrate (None = all)
        user_id: Optional specific user ID to migrate
        dry_run: If True, don't actually migrate
        verbose: If True, log details
        delete_old: If True, delete old files after migration (not implemented yet)

    Returns:
        Dict with migration statistics
    """
    supabase = get_supabase_client()
    stats = {
        "migrated": 0,
        "skipped": 0,
        "errors": 0,
        "no_context": 0
    }

    # Determine which connectors to process
    connectors = connector_types if connector_types else CONNECTOR_TYPES

    # Validate connector names
    invalid_connectors = set(connectors) - set(CONNECTOR_TYPES)
    if invalid_connectors:
        logger.error(f"Invalid connector types: {invalid_connectors}")
        logger.info(f"Valid connectors: {CONNECTOR_TYPES}")
        return stats

    logger.info(f"\n{'='*60}")
    logger.info(f"Storage Migration {'(DRY RUN)' if dry_run else '(EXECUTING)'}")
    logger.info(f"{'='*60}")
    logger.info(f"Connectors: {', '.join(connectors)}")
    if user_id:
        logger.info(f"User ID filter: {user_id}")
    logger.info("")

    # Cache for user contexts
    user_contexts = {}

    # List files to migrate
    logger.info("Scanning for legacy files...")
    files_to_migrate = list_legacy_files(supabase, connectors, user_id)
    logger.info(f"Found {len(files_to_migrate)} files to potentially migrate")

    if not files_to_migrate:
        logger.info("No files need migration.")
        return stats

    # Process each file
    for file_data in files_to_migrate:
        uid = file_data["user_id"]

        # Get user context (cached)
        if uid not in user_contexts:
            user_contexts[uid] = get_user_context(supabase, uid)

        context = user_contexts[uid]

        if not context or not context.get("organization_id"):
            stats["no_context"] += 1
            if verbose:
                logger.warning(f"  Skipping {file_data['original_path']}: no org context for user {uid}")
            continue

        success, message = migrate_file(supabase, file_data, context, dry_run, verbose)

        if success:
            if message == "dry_run":
                stats["migrated"] += 1
            elif message == "migrated":
                stats["migrated"] += 1
            else:
                stats["skipped"] += 1
        else:
            stats["errors"] += 1

        # Stop early in dry run after sampling
        if dry_run and (stats["migrated"] + stats["skipped"] + stats["errors"]) >= 50:
            logger.info("\n[DRY RUN] Sampled 50 files, stopping preview")
            break

    return stats


def print_summary(stats: Dict[str, int], dry_run: bool):
    """Print migration summary."""
    logger.info(f"\n{'='*60}")
    logger.info(f"MIGRATION SUMMARY {'(DRY RUN)' if dry_run else '(COMPLETED)'}")
    logger.info(f"{'='*60}\n")

    logger.info(f"  Files migrated:   {stats.get('migrated', 0)}")
    logger.info(f"  Files skipped:    {stats.get('skipped', 0)}")
    logger.info(f"  Files errored:    {stats.get('errors', 0)}")
    logger.info(f"  No user context:  {stats.get('no_context', 0)}")

    if dry_run:
        logger.info("\n  NOTE: This was a dry run. Use --execute to apply changes.")


def main():
    parser = argparse.ArgumentParser(
        description="Migrate storage paths from legacy format to RBAC-scoped format.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Dry run (preview changes)
    python Backend/scripts/migrate_storage_paths.py

    # Execute the migration
    python Backend/scripts/migrate_storage_paths.py --execute

    # Migrate specific connectors
    python Backend/scripts/migrate_storage_paths.py --execute --connectors google_drive,jira

    # Migrate for specific user
    python Backend/scripts/migrate_storage_paths.py --execute --user-id <UUID>

    # Verbose output
    python Backend/scripts/migrate_storage_paths.py --execute --verbose
        """
    )

    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually execute the migration (default is dry run)"
    )

    parser.add_argument(
        "--connectors",
        type=str,
        help=f"Comma-separated list of connectors to migrate. Default: all. Valid: {','.join(CONNECTOR_TYPES)}"
    )

    parser.add_argument(
        "--user-id",
        type=str,
        help="Migrate files for a specific user ID only"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output for each file"
    )

    args = parser.parse_args()

    # Parse connectors argument
    connectors = None
    if args.connectors:
        connectors = [c.strip() for c in args.connectors.split(",")]

    dry_run = not args.execute

    if not dry_run:
        logger.warning("="*60)
        logger.warning("EXECUTING MIGRATION - THIS WILL MODIFY STORAGE")
        logger.warning("="*60)
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != "yes":
            logger.info("Aborted.")
            return

    # Run the migration
    start_time = datetime.now()
    stats = run_migration(
        connector_types=connectors,
        user_id=args.user_id,
        dry_run=dry_run,
        verbose=args.verbose
    )
    duration = (datetime.now() - start_time).total_seconds()

    # Print summary
    print_summary(stats, dry_run)
    logger.info(f"\n  Duration: {duration:.2f} seconds")


if __name__ == "__main__":
    main()
