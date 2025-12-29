"""
Helper script to add existing users to teams.

Usage:
    python scripts/add_user_to_team.py <user_email>

This will:
1. Find the user by email
2. Check if their organization has a team
3. Create a default team if needed
4. Add the user to the team
"""

import sys
import os
from pathlib import Path

# Add parent directory to path so we can import from core
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import get_db
from psycopg2.extras import RealDictCursor


def add_user_to_team(user_email: str):
    """Add a user to their organization's team (or create one if needed)."""
    
    with get_db() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Find user by email
        print(f"Looking up user: {user_email}")
        cursor.execute(
            """
            SELECT id, first_name, second_name, email, organization_id, role
            FROM users
            WHERE email = %s
            """,
            (user_email,)
        )
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ User not found: {user_email}")
            return False
            
        user_id = user["id"]
        org_id = user["organization_id"]
        print(f"✓ Found user: {user['first_name']} {user['second_name']} (ID: {user_id})")
        
        # 2. Check if user is already in a team
        cursor.execute(
            """
            SELECT COUNT(*) as count
            FROM team_members
            WHERE user_id = %s
            """,
            (user_id,)
        )
        already_in_team = cursor.fetchone()["count"] > 0
        
        if already_in_team:
            print(f"ℹ️  User is already a member of a team")
            cursor.execute(
                """
                SELECT t.name, t.id
                FROM teams t
                JOIN team_members tm ON t.id = tm.team_id
                WHERE tm.user_id = %s
                LIMIT 1
                """,
                (user_id,)
            )
            team = cursor.fetchone()
            print(f"   Team: {team['name']} (ID: {team['id']})")
            return True
        
        # 3. Check if organization has a team
        cursor.execute(
            """
            SELECT id, name
            FROM teams
            WHERE organization_id = %s
            LIMIT 1
            """,
            (org_id,)
        )
        team = cursor.fetchone()
        
        if not team:
            # Create a default team for the organization
            print(f"Creating default team for organization...")
            cursor.execute(
                """
                SELECT name FROM organizations WHERE id = %s
                """,
                (org_id,)
            )
            org = cursor.fetchone()
            team_name = f"{org['name']} Team" if org else "Default Team"
            
            cursor.execute(
                """
                INSERT INTO teams (id, organization_id, name)
                VALUES (gen_random_uuid(), %s, %s)
                RETURNING id, name
                """,
                (org_id, team_name)
            )
            team = cursor.fetchone()
            print(f"✓ Created team: {team['name']} (ID: {team['id']})")
        else:
            print(f"✓ Found existing team: {team['name']} (ID: {team['id']})")
        
        # 4. Add user to the team
        print(f"Adding user to team...")
        cursor.execute(
            """
            INSERT INTO team_members (
                id,
                team_id,
                user_id,
                role,
                performance,
                capacity,
                project_count,
                status
            )
            VALUES (gen_random_uuid(), %s, %s, %s, 85, 80, 0, 'available')
            """,
            (team["id"], user_id, user.get("role") or "Member")
        )
        
        conn.commit()
        print(f"✅ Successfully added {user['first_name']} to {team['name']}")
        print(f"\n📊 Team member details:")
        print(f"   - Role: {user.get('role') or 'Member'}")
        print(f"   - Performance: 85%")
        print(f"   - Capacity: 80%")
        print(f"   - Status: available")
        
        return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/add_user_to_team.py <user_email>")
        print("\nExample:")
        print("  python scripts/add_user_to_team.py john@example.com")
        sys.exit(1)
    
    user_email = sys.argv[1]
    
    try:
        success = add_user_to_team(user_email)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
