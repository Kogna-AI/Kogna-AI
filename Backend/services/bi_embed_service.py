"""
BI Embedding Service
Generates secure embed tokens/URLs for each BI provider.
"""
import time
import jwt
import uuid
import logging
import hashlib
import hmac
import json as json_mod
import urllib.parse
from typing import Dict, Any

logger = logging.getLogger(__name__)


class BIEmbedService:
    """Generate secure embed URLs/tokens for various BI providers."""

    @staticmethod
    async def generate_embed(
        provider: str,
        connector_config: Dict[str, Any],
        dashboard_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route to the correct provider's embed generation."""
        generators = {
            "tableau": BIEmbedService._generate_tableau_embed,
            "powerbi": BIEmbedService._generate_powerbi_embed,
            "looker": BIEmbedService._generate_looker_embed,
            "superset": BIEmbedService._generate_superset_embed,
            "metabase": BIEmbedService._generate_metabase_embed,
        }
        generator = generators.get(provider)
        if not generator:
            raise ValueError(f"Unsupported BI provider: {provider}")
        return await generator(connector_config, dashboard_config)

    # ================================================================
    # Tableau - Connected Apps JWT
    # ================================================================
    @staticmethod
    async def _generate_tableau_embed(
        connector: Dict, dashboard: Dict
    ) -> Dict[str, Any]:
        now = int(time.time())
        payload = {
            "iss": connector.get("api_key"),
            "exp": now + 600,
            "jti": str(uuid.uuid4()),
            "aud": "tableau",
            "sub": connector.get("config", {}).get("username", ""),
            "scp": ["tableau:views:embed", "tableau:views:embed_authoring"],
        }
        token = jwt.encode(
            payload,
            connector.get("api_secret", ""),
            algorithm="HS256",
            headers={
                "kid": connector.get("config", {}).get("secret_id", ""),
                "iss": connector.get("api_key"),
            },
        )
        server = connector.get("server_url", "").rstrip("/")
        ext_id = dashboard.get("external_dashboard_id", "")

        return {
            "embed_url": f"{server}/views/{ext_id}",
            "token": token,
            "token_type": "jwt",
            "expires_at": now + 600,
            "provider": "tableau",
        }

    # ================================================================
    # Power BI - Azure AD Client Credentials
    # ================================================================
    @staticmethod
    async def _generate_powerbi_embed(
        connector: Dict, dashboard: Dict
    ) -> Dict[str, Any]:
        import httpx

        tenant_id = connector.get("tenant_id", "")
        client_id = connector.get("api_key", "")
        client_secret = connector.get("api_secret", "")
        workspace_id = connector.get("workspace_id", "")
        report_id = dashboard.get("external_dashboard_id", "")

        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        async with httpx.AsyncClient() as client:
            # Step 1: Get Azure AD token
            token_resp = await client.post(token_url, data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": "https://analysis.windows.net/powerbi/api/.default",
            })
            if token_resp.status_code != 200:
                raise Exception(f"Power BI auth failed: {token_resp.text}")
            azure_token = token_resp.json()["access_token"]

            # Step 2: Generate embed token
            embed_api_url = (
                f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}"
                f"/reports/{report_id}/GenerateToken"
            )
            embed_resp = await client.post(
                embed_api_url,
                headers={"Authorization": f"Bearer {azure_token}"},
                json={"accessLevel": "View"},
            )
            if embed_resp.status_code != 200:
                raise Exception(f"Power BI embed token failed: {embed_resp.text}")
            embed_data = embed_resp.json()

        return {
            "embed_url": (
                f"https://app.powerbi.com/reportEmbed"
                f"?reportId={report_id}&groupId={workspace_id}"
            ),
            "token": embed_data["token"],
            "token_type": "bearer",
            "expires_at": int(time.time()) + 3600,
            "provider": "powerbi",
        }

    # ================================================================
    # Looker - SSO Signed Embed URL
    # ================================================================
    @staticmethod
    async def _generate_looker_embed(
        connector: Dict, dashboard: Dict
    ) -> Dict[str, Any]:
        server = connector.get("server_url", "").rstrip("/")
        embed_secret = connector.get("embed_secret", "")
        ext_id = dashboard.get("external_dashboard_id", "")

        now = int(time.time())
        nonce = str(uuid.uuid4())
        embed_path = f"/embed/dashboards/{ext_id}"

        params = {
            "nonce": nonce,
            "time": now,
            "session_length": 3600,
            "external_user_id": connector.get("config", {}).get(
                "embed_user_id", "kogna_user"
            ),
            "permissions": ["access_data", "see_looks", "see_user_dashboards"],
            "models": connector.get("config", {}).get("models", []),
            "access_filters": {},
            "force_logout_login": False,
        }
        json_params = json_mod.dumps(params, sort_keys=True)
        string_to_sign = f"\n{server}{embed_path}\n{json_params}"
        signature = hmac.new(
            embed_secret.encode(), string_to_sign.encode(), hashlib.sha256
        ).hexdigest()

        signed_url = (
            f"{server}{embed_path}"
            f"?nonce={nonce}&time={now}&signature={signature}"
            f"&{urllib.parse.urlencode({'params': json_params})}"
        )

        return {
            "embed_url": signed_url,
            "token": None,
            "token_type": "url_signed",
            "expires_at": now + 3600,
            "provider": "looker",
        }

    # ================================================================
    # Apache Superset - Guest Token API
    # ================================================================
    @staticmethod
    async def _generate_superset_embed(
        connector: Dict, dashboard: Dict
    ) -> Dict[str, Any]:
        import httpx

        server = connector.get("server_url", "").rstrip("/")
        username = connector.get("config", {}).get("username", "admin")
        password = connector.get("api_secret", "")
        ext_id = dashboard.get("external_dashboard_id", "")

        async with httpx.AsyncClient() as client:
            # Step 1: Login
            login_resp = await client.post(
                f"{server}/api/v1/security/login",
                json={
                    "username": username,
                    "password": password,
                    "provider": "db",
                },
            )
            if login_resp.status_code != 200:
                raise Exception(f"Superset login failed: {login_resp.text}")
            access_token = login_resp.json()["access_token"]

            # Step 2: Get guest token
            guest_resp = await client.post(
                f"{server}/api/v1/security/guest_token/",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "user": {
                        "username": "kogna_embed",
                        "first_name": "Kogna",
                        "last_name": "Embed",
                    },
                    "resources": [{"type": "dashboard", "id": ext_id}],
                    "rls": [],
                },
            )
            if guest_resp.status_code != 200:
                raise Exception(f"Superset guest token failed: {guest_resp.text}")
            guest_token = guest_resp.json()["token"]

        return {
            "embed_url": f"{server}/superset/dashboard/{ext_id}/?standalone=true",
            "token": guest_token,
            "token_type": "guest_token",
            "expires_at": int(time.time()) + 300,
            "provider": "superset",
        }

    # ================================================================
    # Metabase - Signed Embed URL (JWT)
    # ================================================================
    @staticmethod
    async def _generate_metabase_embed(
        connector: Dict, dashboard: Dict
    ) -> Dict[str, Any]:
        server = connector.get("server_url", "").rstrip("/")
        embed_secret = connector.get("embed_secret", "")
        ext_id = dashboard.get("external_dashboard_id", "")

        now = int(time.time())
        payload = {
            "resource": {"dashboard": int(ext_id)},
            "params": {},
            "exp": now + 600,
        }
        token = jwt.encode(payload, embed_secret, algorithm="HS256")

        return {
            "embed_url": f"{server}/embed/dashboard/{token}#bordered=true&titled=true",
            "token": token,
            "token_type": "jwt",
            "expires_at": now + 600,
            "provider": "metabase",
        }
