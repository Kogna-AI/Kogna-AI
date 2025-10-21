import os
import json
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
from supabase_connect import get_supabase_manager

# Load environment variables
load_dotenv()

supabase = get_supabase_manager()

#Supabase connect: fetch all rows from a table
def test_connection():
    data = supabase.table("metrics").select("*").execute()
    print(data)


def check_existing_files():
    """Check which JSON files actually exist"""
    data_dir = Path("mock_data_large")
    
    if not data_dir.exists():
        print(f"Directory {data_dir} does not exist!")
        return []
    
    existing_files = []
    print("\nChecking for JSON files in mock_data_large/:")
    
    for file in data_dir.glob("*.json"):
        existing_files.append(file.name)
        print(f"Found: {file.name}")
    
    return existing_files

def get_table_list(supabase):
    """Get list of existing tables from database"""
    try:
        # Query to get all table names
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
        """
        result = supabase.rpc('sql_query', {'query': query}).execute()
        return [row['table_name'] for row in result.data]
    except:
        # If RPC doesn't work, return expected tables
        return [
            'organizations', 'users', 'teams', 'team_members', 
            'team_skills', 'data_sources', 'datasets', 'data_records',
            'meetings', 'meeting_attendees', 'objectives', 'growth_stages',
            'milestones', 'metrics', 'ai_insights', 'recommendations',
            'recommendation_reasons', 'actions', 'feedback', 
            'feedback_tags', 'feedback_metrics'
        ]

def upload_only_existing_data():
    """Upload only the JSON files that actually exist"""
    
    # Initialize Supabase client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env file")
        return
    
    supabase: Client = create_client(url, key)
    print(f"Connected to Supabase")

    # Check which files exist
    existing_files = check_existing_files()
    if not existing_files:
        print("No JSON files found to upload!")
        return
    
    # Path to mock data
    data_dir = Path("mock_data_large")
    
    # Define upload mappings ONLY for files that exist
    upload_success = []
    upload_failed = []
    
    # 1. Upload organization.json if it exists
    if "organization.json" in existing_files:
        try:
            with open(data_dir / "organization.json", 'r') as f:
                data = json.load(f)
            
            # Transform for your schema
            record = {
                "id": data.get("id", 1),
                "name": data.get("Name") or data.get("name", "AstraNova Technologies"),
                "industry": data.get("industry", "AI & Data Analytics"),
                "team_due": data.get("team_size", 125),
                "project_number": data.get("project_number", 6),
                "created_at": data.get("created_at")
            }
            
            response = supabase.table("organizations").upsert(record).execute()
            print(f"Uploaded organization")
            upload_success.append("organizations")
        except Exception as e:
            print(f"Error uploading organization: {str(e)}")
            upload_failed.append(("organizations", str(e)))
    
    # 2. Upload teams.json if it exists
    if "teams.json" in existing_files:
        try:
            with open(data_dir / "teams.json", 'r') as f:
                teams_data = json.load(f)
            
            teams_records = []
            for team in teams_data:
                teams_records.append({
                    "id": team.get("id"),
                    "organization_id": team.get("organization_id", 1),
                    "name": team.get("name"),
                    "team_id": f"TEAM-{team.get('id')}",
                    "created_at": team.get("created_at")
                })
            
            if teams_records:
                response = supabase.table("teams").upsert(teams_records).execute()
                print(f"Uploaded {len(teams_records)} teams")
                upload_success.append("teams")
        except Exception as e:
            print(f"Error uploading teams: {str(e)}")
            upload_failed.append(("teams", str(e)))
    
    # 3. Upload users.json if it exists
    if "users.json" in existing_files:
        try:
            with open(data_dir / "users.json", 'r') as f:
                users_data = json.load(f)
            
            users_records = []
            for user in users_data:
                email = f"{user.get('first_name', 'user').lower()}.{user.get('second_name', 'example').lower()}@astranova.com"
                users_records.append({
                    "id": user.get("id"),
                    "organization_id": user.get("organization_id", 1),
                    "first_name": user.get("first_name"),
                    "second_name": user.get("second_name"),
                    "role": user.get("role"),
                    "email": email,
                    "created_at": user.get("created_at")
                })
            
            if users_records:
                # Upload in batches to avoid conflicts
                batch_size = 20
                for i in range(0, len(users_records), batch_size):
                    batch = users_records[i:i + batch_size]
                    response = supabase.table("users").upsert(batch).execute()
                print(f"Uploaded {len(users_records)} users")
                upload_success.append("users")
        except Exception as e:
            print(f"Error uploading users: {str(e)}")
            upload_failed.append(("users", str(e)))
    
    # Continue with other files that exist...
    # Add similar blocks for each file that exists in your directory
    
    # Print summary
    print("\n" + "="*50)
    print("UPLOAD SUMMARY")
    print("="*50)
    print(f"Successfully uploaded: {len(upload_success)} tables")
    for table in upload_success:
        print(f"   - {table}")
    
    if upload_failed:
        print(f"\nFailed uploads: {len(upload_failed)} tables")
        for table, error in upload_failed:
            print(f"   - {table}: {error[:100]}...")
    
    # Verify the data
    print("\nVerifying data in database:")
    tables_to_check = ["organizations", "teams", "users", "team_members"]
    
    for table in tables_to_check:
        try:
            result = supabase.table(table).select("*", count="exact").execute()
            print(f"{table}: {result.count} records")
        except Exception as e:
            print(f"{table}: Unable to count - {str(e)[:50]}")

if __name__ == "__main__":
    print("Starting Supabase data upload...")
    print("="*50)
    upload_only_existing_data()