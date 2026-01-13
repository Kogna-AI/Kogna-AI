import os
from supabase import create_client, Client
from typing import Optional, List, Dict, Any
import json
from datetime import datetime
from supabase import create_client, Client

class SupabaseManager:
    def __init__(self):
        """Initialize Supabase client with environment variables"""
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.url or not self.key:
            raise ValueError("Supabase credentials not found in environment variables")
        
        self.client: Client = create_client(self.url, self.key)

    
    
    def upload_mock_data(self, data_dir: str = "Backend/Ai_agents/mock_data_large"):
        """Upload mock data to Supabase with data transformation for schema compatibility"""
        
        # Map JSON files to database tables with any necessary transformations
        file_mappings = [
            ("organization.json", "organizations", self._transform_organization),
            ("teams.json", "teams", self._transform_teams),
            ("users.json", "users", self._transform_users),
            ("team_members.json", "team_members", self._transform_team_members),
            ("team_skills.json", "team_skills", self._transform_team_skills),
            ("data_sources.json", "data_sources", None),
            ("datasets.json", "datasets", None),
            ("data_records.json", "data_records", None),
            ("metrics.json", "metrics", None),
            ("objectives.json", "objectives", None),
            ("meetings.json", "meetings", self._transform_meetings),
            ("feedback.json", "feedback", self._transform_feedback),
            ("feedback_tags.json", "feedback_tags", None),
            ("feedback_metrics.json", "feedback_metrics", None),
        ]
        
        for filename, table_name, transform_func in file_mappings:
            file_path = os.path.join(data_dir, filename)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    # Apply transformation if needed
                    if transform_func:
                        data = transform_func(data)
                    
                    # Handle single record vs array
                    if isinstance(data, dict):
                        records = [data]
                    else:
                        records = data
                    
                    # Upload in batches
                    batch_size = 50
                    for i in range(0, len(records), batch_size):
                        batch = records[i:i + batch_size]
                        response = self.client.table(table_name).insert(batch).execute()
                    
                    print(f"Uploaded {len(records)} records to {table_name}")
                    
                except Exception as e:
                    print(f"Error uploading {filename}: {str(e)}")
    
    def _transform_organization(self, data):
        """Transform organization data to match schema"""
        if isinstance(data, dict):
            # Add missing fields with defaults
            data['team_due'] = data.get('team_size', 0)
            data['team'] = data.get('industry', 'Technology')
            # Remove team_size as it's now team_due
            if 'team_size' in data:
                del data['team_size']
        return data
    
    def _transform_teams(self, data):
        """Transform teams data to match schema"""
        for team in (data if isinstance(data, list) else [data]):
            team['team_id'] = f"TEAM-{team['id']}"
        return data
    
    def _transform_users(self, data):
        """Transform users data to match schema"""
        for user in (data if isinstance(data, list) else [data]):
            # Generate email if not present
            if 'email' not in user:
                fname = user.get('first_name', 'user').lower()
                sname = user.get('second_name', 'example').lower()
                user['email'] = f"{fname}.{sname}@astranova.com"
        return data
    
    def _transform_team_members(self, data):
        """Transform team_members data to match schema"""
        for member in (data if isinstance(data, list) else [data]):
            # Convert performance and capacity to percentage (0-100)
            if 'performance' in member:
                member['performance'] = member['performance'] * 100
            if 'capacity' in member:
                member['capacity'] = member['capacity'] * 100
        return data
    
    def _transform_team_skills(self, data):
        """Transform team_skills data to match schema"""
        for skill in (data if isinstance(data, list) else [data]):
            # Convert numeric proficiency to categorical
            prof_value = skill.get('proficiency', 0.5)
            if prof_value < 0.25:
                skill['proficiency'] = 'beginner'
            elif prof_value < 0.5:
                skill['proficiency'] = 'intermediate'
            elif prof_value < 0.75:
                skill['proficiency'] = 'advanced'
            else:
                skill['proficiency'] = 'expert'
        return data
    
    def _transform_meetings(self, data):
        """Transform meetings data to match schema"""
        for meeting in (data if isinstance(data, list) else [data]):
            # Remove action_items as it's not in the meetings table
            if 'action_items' in meeting:
                del meeting['action_items']
            # Remove content as it's not in the meetings table
            if 'content' in meeting:
                del meeting['content']
        return data
    
    def _transform_feedback(self, data):
        """Transform feedback data to match schema"""
        for feedback in (data if isinstance(data, list) else [data]):
            # Rename fields
            if 'comment' in feedback:
                feedback['comments'] = feedback.pop('comment')
            if 'written_at' in feedback:
                feedback['version_at'] = feedback.pop('written_at')
        return data
    
    def query_data(self, table: str, filters: Dict = None, limit: int = None) -> List[Dict]:
        """Query data from Supabase table"""
        query = self.client.table(table).select("*")
        
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        
        if limit:
            query = query.limit(limit)
        
        response = query.execute()
        return response.data
    
    def search_documents(self, query: str) -> Dict[str, Any]:
        """Smart search across multiple tables based on query content"""
        results = {}
        query_lower = query.lower()
        
        # Enhanced keyword mapping for better search
        search_mappings = [
            # People and teams
            (["employee", "user", "person", "staff"], "users"),
            (["team", "department", "group"], "teams"),
            (["member", "capacity", "performance"], "team_members"),
            (["skill", "proficiency", "expertise"], "team_skills"),
            
            # Projects and objectives
            (["project", "objective", "goal", "okr"], "objectives"),
            (["milestone", "achievement"], "milestones"),
            (["growth", "stage"], "growth_stages"),
            
            # Meetings and collaboration
            (["meeting", "sync", "standup", "discussion"], "meetings"),
            (["attendee", "participant"], "meeting_attendees"),
            
            # Data and metrics
            (["metric", "kpi", "measurement", "performance"], "metrics"),
            (["data", "dataset", "source"], "datasets"),
            (["record", "entry"], "data_records"),
            
            # Feedback and insights
            (["feedback", "comment", "rating", "review"], "feedback"),
            (["insight", "analysis", "finding"], "ai_insights"),
            (["recommendation", "suggestion", "advice"], "recommendations"),
            (["action", "task", "todo"], "actions"),
            
            # Organization
            (["organization", "company", "business"], "organizations"),
        ]
        
        # Search based on keywords found in query
        tables_to_search = set()
        for keywords, table in search_mappings:
            if any(keyword in query_lower for keyword in keywords):
                tables_to_search.add(table)
        
        # If no specific keywords, search common tables
        if not tables_to_search:
            tables_to_search = {"users", "teams", "objectives", "metrics", "meetings"}
        
        # Execute searches
        for table in tables_to_search:
            try:
                # For text searches, we can use Supabase's text search if columns are indexed
                data = self.query_data(table, limit=100)
                if data:
                    results[table] = data
            except Exception as e:
                print(f"Error searching {table}: {e}")
        
        return results
    
    def get_team_performance_summary(self, organization_id: int = None):
        """Get team performance summary using the view"""
        try:
            query = self.client.table("team_performance_summary").select("*")
            if organization_id:
                query = query.eq("organization_id", organization_id)
            response = query.execute()
            return response.data
        except Exception as e:
            print(f"Error getting team performance: {e}")
            return []
    
    def get_organization_dashboard(self, organization_id: int = None):
        """Get organization dashboard data using the view"""
        try:
            query = self.client.table("organization_dashboard").select("*")
            if organization_id:
                query = query.eq("id", organization_id)
            response = query.execute()
            return response.data
        except Exception as e:
            print(f"Error getting dashboard: {e}")
            return []
    
    def create_ai_insight(self, organization_id: int, category: str, 
                         title: str, description: str, confidence: float = 80.0):
        """Create a new AI insight"""
        try:
            data = {
                "organization_id": organization_id,
                "category": category,
                "title": title,
                "description": description,
                "confidence": confidence,
                "level": "high" if confidence > 75 else "medium" if confidence > 50 else "low",
                "status": "active"
            }
            response = self.client.table("ai_insights").insert(data).execute()
            return response.data
        except Exception as e:
            print(f"Error creating insight: {e}")
            return None
    
    def create_recommendation(self, organization_id: int, title: str, 
                            recommendation: str, action: str, confidence: float = 75.0):
        """Create a new recommendation"""
        try:
            data = {
                "organization_id": organization_id,
                "title": title,
                "recommendation": recommendation,
                "action": action,
                "confidence": confidence,
                "status": "pending"
            }
            response = self.client.table("recommendations").insert(data).execute()
            return response.data
        except Exception as e:
            print(f"Error creating recommendation: {e}")
            return None

# Singleton instance
_supabase_manager = None

def get_supabase_manager() -> SupabaseManager:
    """
    Get or create the singleton SupabaseManager instance.
    """
    global _supabase_manager
    if _supabase_manager is None:
        _supabase_manager = SupabaseManager()
    return _supabase_manager

