from __future__ import annotations

import os
import time
from typing import Any, Dict

from cozepy import JWTOAuthApp, COZE_CN_BASE_URL
from dotenv import load_dotenv

load_dotenv()

DEFAULT_API_BASE = os.getenv("COZE_API_BASE", COZE_CN_BASE_URL)
DEFAULT_TOKEN_TTL = int(os.getenv("COZE_ACCESS_TOKEN_TTL", "3600"))


def _read_private_key() -> str:
    private_key = os.getenv("COZE_JWT_OAUTH_PRIVATE_KEY")
    private_key_path = os.getenv("COZE_JWT_OAUTH_PRIVATE_KEY_FILE_PATH")

    if private_key_path:
        with open(private_key_path, "r", encoding="utf-8") as fp:
            private_key = fp.read()

    if not private_key:
        raise RuntimeError("Missing COZE_JWT_OAUTH_PRIVATE_KEY or _FILE_PATH")

    return private_key.replace("\\n", "\n")


def _get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    return value


class OAuthConfig:
    """Wrapper around cozepy JWTOAuthApp for session-scoped token issuance."""
    
    def __init__(self, jwt_app: JWTOAuthApp):
        self.jwt_app = jwt_app
    
    @classmethod
    def from_env(cls) -> "OAuthConfig":
        client_id = _get_required_env("COZE_JWT_OAUTH_CLIENT_ID")
        public_key_id = _get_required_env("COZE_JWT_OAUTH_PUBLIC_KEY_ID")
        private_key = _read_private_key()
        base_url = os.getenv("COZE_API_BASE", COZE_CN_BASE_URL)
        
        jwt_app = JWTOAuthApp(
            client_id=client_id,
            private_key=private_key,
            public_key_id=public_key_id,
            base_url=base_url,
        )
        return cls(jwt_app)
    
    def issue_access_token(self, session_name: str, ttl: int = DEFAULT_TOKEN_TTL) -> Dict[str, Any]:
        """Issue a session-scoped OAuth access token."""
        # Use cozepy SDK to get token with session_name
        oauth_token = self.jwt_app.get_access_token(ttl=ttl, session_name=session_name)
        
        return {
            "access_token": oauth_token.access_token,
            "token_type": oauth_token.token_type,
            "expires_in": oauth_token.expires_in,
            "expires_at": int(time.time()) + oauth_token.expires_in,
        }

