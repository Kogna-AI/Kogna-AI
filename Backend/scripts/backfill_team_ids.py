#!/usr/bin/env python3
"""
Backfill team_id for existing KPI records based on user's primary team.

This script updates records in KPI-related tables where team_id is NULL,
assigning the user's primary team_id from the team_members table.

Usage:
    # Dry run (default) - shows what would be updated
    python Backend/scripts/backfill_team_ids.py

    # Execute the backfill
    python Backend/scripts/backfill_team_ids.py --execute

    # Backfill specific tables only
    python Backend/scripts/backfill_team_ids.py --execute --tables connector_kpis,sync_jobs

    # Verbose output
    python Backend/scripts/backfill_team_ids.py --execute --verbose
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Optional

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

# Tables to backfill with team_id
TABLES_TO_BACKFILL = [
    "connector_kpis",
    "agent_performance_metrics",
    "user_engagement_metrics",
    "rag_quality_metrics",
    "sync_jobs",
    "agent_traces",
    "audit_logs",
    "user_connectors",
]


def get_supabase_client():
    """Get Supabase client instance."""
    return get_supabase_manager().client


def get_users_primary_teams(supabase) -> Dict[str, str]:
    """
    Fetch all users' primary team mappings.

    Returns:
        Dict mapping user_id -> primary team_id
    """
    logger.info("Fetching user primary team mappings...")

    response = supabase.table("team_members") \
        .select("user_id, team_id") \
        .eq("is_primary", True) \
        .execute()

    mappings = {}
    for row in response.data or []:
        user_id = row.get("user_id")
        team_id = row.get("team_id")
        if user_id and team_id:
            mappings[user_id] = team_id

    logger.info(f"Found {len(mappings)} users with primary teams")
    return mappings


def count_null_team_ids(supabase, table_name: str) -> int:
    """Count records with NULL team_id in a table."""
    try:
        response = supabase.table(table_name) \
            .select("id", count="exact") \
            .is_("team_id", "null") \
            .execute()
        return response.count or 0
    except Exception as e:
        logger.warning(f"Could not count NULL team_ids in {table_name}: {e}")
        return 0


def get_records_to_update(supabase, table_name: str, limit: int = 1000) -> List[Dict]:
    """
    Get records with NULL team_id that have a user_id we can map.

    Args:
        supabase: Supabase client
        table_name: Table to query
        limit: Max records to fetch per batch

    Returns:
        List of records with id and user_id
    """
    try:
        response = supabase.table(table_name) \
            .select("id, user_id") \
            .is_("team_id", "null") \
            .not_.is_("user_id", "null") \
            .limit(limit) \
            .execute()
        return response.data or []
    except Exception as e:
        logger.warning(f"Could not fetch records from {table_name}: {e}")
        return []


def backfill_table(
    supabase,
    table_name: str,
    user_team_mappings: Dict[str, str],
    dry_run: bool = True,
    verbose: bool = False
) -> Dict[str, int]:
    """
    Backfill team_id for a single table.

    Args:
        supabase: Supabase client
        table_name: Table to backfill
        user_team_mappings: Dict of user_id -> team_id
        dry_run: If True, don't actually update
        verbose: If True, log each update

    Returns:
        Dict with 'updated', 'skipped', 'errors' counts
    """
    stats = {"updated": 0, "skipped": 0, "errors": 0}

    # Count total NULL records
    null_count = count_null_team_ids(supabase, table_name)
    if null_count == 0:
        logger.info(f"  {table_name}: No records with NULL team_id")
        return stats

    logger.info(f"  {table_name}: {null_count} records with NULL team_id")

    # Process in batches
    batch_size = 500
    total_processed = 0

    while total_processed < null_count:
        records = get_records_to_update(supabase, table_name, limit=batch_size)
        if not records:
            break

        for record in records:
            record_id = record.get("id")
            user_id = record.get("user_id")

            if not user_id:
                stats["skipped"] += 1
                continue

            team_id = user_team_mappings.get(user_id)
            if not team_id:
                # User has no primary team
                stats["skipped"] += 1
                if verbose:
                    logger.debug(f"    Skipping {record_id}: user {user_id} has no primary team")
                continue

            if dry_run:
                stats["updated"] += 1
                if verbose:
                    logger.info(f"    [DRY RUN] Would update {record_id}: team_id = {team_id}")
            else:
                try:
                    supabase.table(table_name) \
                        .update({"team_id": team_id}) \
                        .eq("id", record_id) \
                        .execute()
                    stats["updated"] += 1
                    if verbose:
                        logger.info(f"    Updated {record_id}: team_id = {team_id}")
                except Exception as e:
                    stats["errors"] += 1
                    logger.error(f"    Failed to update {record_id}: {e}")

        total_processed += len(records)

        # Break if we've processed all or hit a dry run limit
        if dry_run and total_processed >= 100:
            logger.info(f"    [DRY RUN] Sampled {total_processed} records, stopping preview")
            break

    return stats


def run_backfill(
    tables: Optional[List[str]] = None,
    dry_run: bool = True,
    verbose: bool = False
) -> Dict[str, Dict[str, int]]:
    """
    Run the backfill process for specified tables.

    Args:
        tables: List of tables to backfill (None = all)
        dry_run: If True, don't actually update
        verbose: If True, log each update

    Returns:
        Dict mapping table_name -> stats
    """
    supabase = get_supabase_client()
    results = {}

    # Determine which tables to process
    tables_to_process = tables if tables else TABLES_TO_BACKFILL

    # Validate table names
    invalid_tables = set(tables_to_process) - set(TABLES_TO_BACKFILL)
    if invalid_tables:
        logger.error(f"Invalid table names: {invalid_tables}")
        logger.info(f"Valid tables: {TABLES_TO_BACKFILL}")
        return results

    # Get user -> team mappings
    user_team_mappings = get_users_primary_teams(supabase)
    if not user_team_mappings:
        logger.warning("No user-team mappings found. Nothing to backfill.")
        return results

    # Process each table
    logger.info(f"\n{'='*60}")
    logger.info(f"Starting backfill {'(DRY RUN)' if dry_run else '(EXECUTING)'}")
    logger.info(f"{'='*60}\n")

    for table_name in tables_to_process:
        logger.info(f"Processing {table_name}...")
        try:
            stats = backfill_table(
                supabase,
                table_name,
                user_team_mappings,
                dry_run=dry_run,
                verbose=verbose
            )
            results[table_name] = stats
        except Exception as e:
            logger.error(f"Failed to process {table_name}: {e}")
            results[table_name] = {"updated": 0, "skipped": 0, "errors": 1}

    return results


def print_summary(results: Dict[str, Dict[str, int]], dry_run: bool):
    """Print a summary of the backfill results."""
    logger.info(f"\n{'='*60}")
    logger.info(f"BACKFILL SUMMARY {'(DRY RUN)' if dry_run else '(COMPLETED)'}")
    logger.info(f"{'='*60}\n")

    total_updated = 0
    total_skipped = 0
    total_errors = 0

    for table_name, stats in results.items():
        updated = stats.get("updated", 0)
        skipped = stats.get("skipped", 0)
        errors = stats.get("errors", 0)

        total_updated += updated
        total_skipped += skipped
        total_errors += errors

        status = "OK" if errors == 0 else "ERRORS"
        logger.info(f"  {table_name}: {updated} updated, {skipped} skipped, {errors} errors [{status}]")

    logger.info(f"\n  TOTAL: {total_updated} updated, {total_skipped} skipped, {total_errors} errors")

    if dry_run:
        logger.info("\n  NOTE: This was a dry run. Use --execute to apply changes.")


def main():
    parser = argparse.ArgumentParser(
        description="Backfill team_id for existing KPI records based on user's primary team.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Dry run (preview changes)
    python Backend/scripts/backfill_team_ids.py

    # Execute the backfill
    python Backend/scripts/backfill_team_ids.py --execute

    # Backfill specific tables
    python Backend/scripts/backfill_team_ids.py --execute --tables connector_kpis,sync_jobs

    # Verbose output
    python Backend/scripts/backfill_team_ids.py --execute --verbose
        """
    )

    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually execute the backfill (default is dry run)"
    )

    parser.add_argument(
        "--tables",
        type=str,
        help=f"Comma-separated list of tables to backfill. Default: all. Valid: {','.join(TABLES_TO_BACKFILL)}"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output for each record"
    )

    args = parser.parse_args()

    # Parse tables argument
    tables = None
    if args.tables:
        tables = [t.strip() for t in args.tables.split(",")]

    dry_run = not args.execute

    if not dry_run:
        logger.warning("="*60)
        logger.warning("EXECUTING BACKFILL - THIS WILL MODIFY DATA")
        logger.warning("="*60)
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != "yes":
            logger.info("Aborted.")
            return

    # Run the backfill
    start_time = datetime.now()
    results = run_backfill(tables=tables, dry_run=dry_run, verbose=args.verbose)
    duration = (datetime.now() - start_time).total_seconds()

    # Print summary
    print_summary(results, dry_run)
    logger.info(f"\n  Duration: {duration:.2f} seconds")


if __name__ == "__main__":
    main()
