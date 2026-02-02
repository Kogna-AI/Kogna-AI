"""Team access validation helpers for RBAC"""

from fastapi import HTTPException, status
from psycopg2.extras import RealDictCursor
from typing import List, Optional


def verify_user_team_access(user_id: str, team_id: str, db) -> bool:
    """
    Verify user has access to the requested team.

    Args:
        user_id: The user's UUID
        team_id: The team UUID to check access for
        db: Database connection context manager

    Returns:
        True if user has access

    Raises:
        HTTPException 403 if user does not have access to the team
    """
    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT 1 FROM team_members
            WHERE user_id = %s AND team_id = %s
        """, (user_id, team_id))

        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: You do not have access to team {team_id}"
            )
    return True


def get_user_primary_team(user_id: str, db) -> Optional[str]:
    """
    Get user's primary team ID.

    Args:
        user_id: The user's UUID
        db: Database connection context manager

    Returns:
        The primary team's UUID as string, or None if user has no primary team
    """
    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT team_id FROM team_members
            WHERE user_id = %s AND is_primary = TRUE
            LIMIT 1
        """, (user_id,))

        result = cursor.fetchone()
    return str(result["team_id"]) if result else None


def get_user_team_ids(user_id: str, db) -> List[str]:
    """
    Get all team IDs that a user belongs to.

    Args:
        user_id: The user's UUID
        db: Database connection context manager

    Returns:
        List of team UUIDs as strings
    """
    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT team_id FROM team_members
            WHERE user_id = %s
            ORDER BY is_primary DESC, joined_at ASC
        """, (user_id,))

        results = cursor.fetchall()
    return [str(row["team_id"]) for row in results]


def verify_team_organization_match(team_id: str, organization_id: str, db) -> bool:
    """
    Verify that a team belongs to the specified organization.

    Args:
        team_id: The team UUID to verify
        organization_id: The organization UUID to check against
        db: Database connection context manager

    Returns:
        True if team belongs to organization

    Raises:
        HTTPException 403 if team does not belong to organization
    """
    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT 1 FROM teams
            WHERE id = %s AND organization_id = %s
        """, (team_id, organization_id))

        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Team {team_id} does not belong to your organization"
            )
    return True
