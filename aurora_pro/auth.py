"""Authentication and authorization middleware for Aurora Pro."""
import os
import secrets
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader, APIKeyQuery
from pydantic import BaseModel


API_KEY_NAME = "X-Aurora-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)


class APIKeyStore:
    """Simple in-memory API key store with role-based access."""

    def __init__(self):
        self.keys = {}
        # Generate default admin key from env or create new one
        admin_key = os.getenv("AURORA_ADMIN_KEY", secrets.token_urlsafe(32))
        self.keys[admin_key] = {"role": "admin", "name": "admin"}
        self._admin_key = admin_key

    def validate(self, api_key: str) -> Optional[dict]:
        return self.keys.get(api_key)

    def create_key(self, name: str, role: str = "user") -> str:
        key = secrets.token_urlsafe(32)
        self.keys[key] = {"role": role, "name": name}
        return key

    def revoke_key(self, api_key: str) -> bool:
        if api_key in self.keys:
            del self.keys[api_key]
            return True
        return False

    def list_keys(self) -> list:
        return [
            {"key": key[:8] + "..." + key[-4:], "name": data["name"], "role": data["role"]}
            for key, data in self.keys.items()
        ]

    def get_admin_key(self) -> str:
        """Return admin key for bootstrapping."""
        return self._admin_key


# Global key store
key_store = APIKeyStore()


async def get_api_key(
    api_key_header: str = Security(api_key_header),
    api_key_query: str = Security(api_key_query),
) -> str:
    """Extract API key from header or query parameter."""
    api_key = api_key_header or api_key_query

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    key_data = key_store.validate(api_key)
    if not key_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key


async def require_admin(api_key: str = Security(get_api_key)) -> str:
    """Require admin role for endpoint access."""
    key_data = key_store.validate(api_key)
    if not key_data or key_data.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return api_key


class APIKeyCreate(BaseModel):
    name: str
    role: str = "user"


class APIKeyResponse(BaseModel):
    key: str
    name: str
    role: str


__all__ = ["get_api_key", "require_admin", "key_store", "APIKeyCreate", "APIKeyResponse"]