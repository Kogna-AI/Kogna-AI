# supabase_connect.py
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class SupabaseManager:
    """
    Simple manager for creating and reusing a Supabase client.
    Reads SUPABASE_URL and SUPABASE_ANON_KEY from .env
    """
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_SERVICE_KEY")
        if not self.url or not self.key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in environment variables.")
        self.client: Client = create_client(self.url, self.key)

# Singleton instance cache
_supabase_manager = None

def get_supabase_manager() -> SupabaseManager:
    """
    Returns a singleton SupabaseManager instance so you don’t 
    re-create the client every time you import it.
    """
    global _supabase_manager
    if _supabase_manager is None:
        _supabase_manager = SupabaseManager()
    return _supabase_manager
