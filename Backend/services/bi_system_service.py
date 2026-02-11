import os
import jwt
import time
import uuid
import httpx  # <--- Make sure this is imported
from typing import Dict, List, Optional
from datetime import datetime
from supabase import create_client, Client

class BISystemService:
    """Integrated Service for Managing BI Metadata and SDK Token Generation"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # Tableau Credentials
        self.tableau_client_id = os.getenv("TABLEAU_CLIENT_ID")
        self.tableau_secret_id = os.getenv("TABLEAU_SECRET_ID")
        self.tableau_secret_value = os.getenv("TABLEAU_SECRET_VALUE")
        
        # We need these to swap the refresh token
        self.microsoft_client_id = os.getenv("MICROSOFT_CLIENT_ID")
        self.microsoft_client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")

        self.bi_configs = {
            'powerbi': {'name': 'Power BI', 'icon': '📊', 'default_url': 'https://app.powerbi.com', 'requires_custom_url': False},
            'tableau': {'name': 'Tableau', 'icon': '📈', 'default_url': None, 'requires_custom_url': True},
            'looker': {'name': 'Looker', 'icon': '🔍', 'default_url': None, 'requires_custom_url': True},
            'metabase': {'name': 'Metabase', 'icon': '📉', 'default_url': None, 'requires_custom_url': True},
            'grafana': {'name': 'Grafana', 'icon': '📊', 'default_url': None, 'requires_custom_url': True},
            'google-drive': {'name': 'Google Drive', 'icon': '📁', 'default_url': None, 'requires_custom_url': False}
        }

    # ============================================
    # TOKEN FACTORY METHODS
    # ============================================

    async def _exchange_refresh_token_for_pbi(self, refresh_token: str) -> str:
        """
        Swaps a generic Refresh Token for a fresh Access Token with Power BI permissions.
        """
        async with httpx.AsyncClient() as client:
            try:
                # FIX: We must use the FULLY QUALIFIED URL for Power BI scopes
                # Microsoft will reject shorthand names during a refresh call.
                pbi_scopes = (
                    "https://analysis.windows.net/powerbi/api/Report.Read.All "
                    "https://analysis.windows.net/powerbi/api/Dataset.Read.All"
                )

                response = await client.post(
                    "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                    data={
                        "client_id": self.microsoft_client_id,
                        "client_secret": self.microsoft_client_secret,
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                        "scope": pbi_scopes 
                    },
                )
                
                if response.status_code != 200:
                    print(f"Token Refresh Error: {response.text}")
                    raise Exception("Failed to refresh Power BI token")
                
                data = response.json()
                return data["access_token"]
            except Exception as e:
                print(f"PBI Token Error: {e}")
                raise e
            
            
    async def get_user_powerbi_reports(self, user_id: str) -> List[Dict]:
        """
        Fetches a list of all Power BI reports accessible to the user.
        """
        # 1. Get a fresh Power BI token (Reusing the logic we just fixed!)
        try:
            access_token = await self.get_powerbi_token(user_id)
        except Exception as e:
            print(f"Token Error: {e}")
            return []

        # 2. Call Power BI API to get reports
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.powerbi.com/v1.0/myorg/reports",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                print(f"Failed to fetch reports: {response.text}")
                return []
            
            data = response.json()
            reports = data.get("value", [])
            
            # 3. Clean up the data for the frontend
            return [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "webUrl": r["webUrl"],
                    # Some reports are in "My Workspace" (no datasetWorkspaceId), others in Groups
                    # We prioritize datasetWorkspaceId, but might need to fetch groups if it's missing.
                    # For now, we extract workspace ID from the embedUrl or datasetWorkspaceId
                    "workspaceId": r.get("datasetWorkspaceId") or "myworkspace" 
                }
                for r in reports
            ]

    async def get_powerbi_token(self, user_id: str) -> str:
        """
        Fetches the USER'S OAuth token from the 'user_connectors' table
        and converts it to a Power BI usable token.
        """
        # 1. Fetch the refresh_token stored by connect.py
        result = self.supabase.table('user_connectors')\
            .select('refresh_token')\
            .eq('user_id', user_id)\
            .eq('service', 'microsoft')\
            .single()\
            .execute()

        # 2. Handle "Not Connected" case
        if not result.data or not result.data.get('refresh_token'):
            raise Exception("User has not connected Microsoft account or token is expired. Please Re-Connect.")

        # 3. Generate a fresh Power BI-specific token
        # We don't use the stored access_token because it might be for Graph API (Files).
        return await self._exchange_refresh_token_for_pbi(result.data['refresh_token'])

    def get_tableau_jwt(self, user_email: str) -> str:
        """Generates a JWT for Tableau Connected Apps"""
        payload = {
            "iss": self.tableau_client_id,
            "exp": int(time.time()) + 600,
            "jti": str(uuid.uuid4()),
            "aud": "tableau",
            "sub": user_email,
            "scp": ["tableau:views:embed", "tableau:metrics:embed"]
        }
        headers = {"kid": self.tableau_secret_id, "iss": self.tableau_client_id}
        return jwt.encode(payload, self.tableau_secret_value, algorithm="HS256", headers=headers)

    # ============================================
    # PUBLIC API METHODS
    # ============================================

    async def get_bi_system_url(self, bi_system_id: str, user_id: str) -> Dict:
        """Returns full SDK configuration including dynamic tokens"""
        # Fetch user info
        user_res = self.supabase.table('users').select('organization_id', 'email').eq('id', user_id).single().execute()
        if not user_res.data:
            raise ValueError(f"User {user_id} not found")

        # Fetch BI system metadata
        bi_res = self.supabase.table('customer_bi_systems')\
            .select('*')\
            .eq('id', bi_system_id)\
            .eq('organization_id', user_res.data['organization_id'])\
            .eq('is_active', True)\
            .single()\
            .execute()
        
        if not bi_res.data:
            raise ValueError("BI system not found or access denied")

        tool_type = bi_res.data['bi_tool']
        
        # Prepare response base
        response_data = {
            "id": bi_res.data['id'],
            "bi_tool": tool_type,
            "reportId": bi_res.data.get('report_id'), 
            "embedUrl": bi_res.data['base_url'],
            "display_name": bi_res.data['display_name'],
            "icon_emoji": bi_res.data['icon_emoji']
        }

        # Inject dynamic tokens
        if tool_type == 'powerbi':
            # This now returns a dedicated Power BI token
            response_data["accessToken"] = await self.get_powerbi_token(user_id)
            response_data["tokenType"] = "Aad"
            
            # Construct the specific Embed URL
            if bi_res.data.get('report_id'):
                r_id = bi_res.data['report_id']
                w_id = bi_res.data.get('workspace_id')
                response_data["embedUrl"] = f"https://app.powerbi.com/reportEmbed?reportId={r_id}"
                if w_id:
                    response_data["embedUrl"] += f"&groupId={w_id}"
                    
        elif tool_type == 'tableau':
            response_data["accessToken"] = self.get_tableau_jwt(user_res.data['email'])

        # Log access
        self._log_access(user_id, bi_system_id)
        self.supabase.table('customer_bi_systems').update({'last_accessed_at': datetime.now().isoformat()}).eq('id', bi_system_id).execute()

        return response_data

    def add_bi_system(self, organization_id: str, bi_tool: str, 
                      report_id: Optional[str] = None,
                      workspace_id: Optional[str] = None,
                      embed_code: Optional[str] = None, 
                      custom_url: Optional[str] = None, 
                      thumbnail_url: Optional[str] = None) -> Dict:
        if bi_tool not in self.bi_configs:
            raise ValueError(f"Unsupported BI tool: {bi_tool}")
        
        config = self.bi_configs[bi_tool]
        base_url = custom_url if custom_url else config.get('default_url')
        
        result = self.supabase.table('customer_bi_systems').upsert({
            'organization_id': organization_id,
            'bi_tool': bi_tool,
            'report_id': report_id,
            'workspace_id': workspace_id,
            'base_url': base_url,
            'embed_code': embed_code,
            'thumbnail_url': thumbnail_url,
            'display_name': config['name'],
            'icon_emoji': config['icon'],
            'is_active': True
        }, on_conflict='organization_id,bi_tool').execute()
        
        return result.data[0]

    def get_user_bi_systems(self, user_id: str) -> List[Dict]:
        user = self.supabase.table('users').select('organization_id').eq('id', user_id).single().execute()
        if not user.data: return []
        
        result = self.supabase.table('customer_bi_systems')\
            .select('*').eq('organization_id', user.data['organization_id'])\
            .eq('is_active', True).order('created_at').execute()
        return result.data

    def get_available_bi_tools(self) -> List[Dict]:
        return [
            {'id': tid, 'name': cfg['name'], 'icon': cfg['icon'], 'requires_custom_url': cfg['requires_custom_url']}
            for tid, cfg in self.bi_configs.items()
        ]

    def _log_access(self, user_id: str, bi_system_id: str):
        try:
            self.supabase.table('bi_system_access_log').insert({
                'user_id': user_id,
                'bi_system_id': bi_system_id,
                'accessed_at': datetime.now().isoformat()
            }).execute()
        except:
            pass