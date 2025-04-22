"""
Security utilities for the SkyReader TTY Message Parser.
"""
import secrets
import time
from typing import Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from app.core.config import get_settings, Settings
from app.core.logging import get_logger

# Configure logger
logger = get_logger(__name__)

# API Key header schema
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# In-memory token cache (for future use)
# In a production environment, this should be a database or Redis
API_KEYS: Dict[str, Dict] = {}


def create_api_key() -> str:
    """
    Create a new API key.

    Returns:
        str: A new random API key
    """
    return secrets.token_urlsafe(32)


def register_api_key(name: str, permissions: Optional[Dict] = None) -> str:
    """
    Register a new API key.

    Args:
        name: Name or identifier for the key
        permissions: Optional permissions for the key

    Returns:
        str: The newly created API key
    """
    api_key = create_api_key()

    API_KEYS[api_key] = {
        "name": name,
        "created_at": time.time(),
        "permissions": permissions or {},
        "rate_limit": 100,  # Default rate limit
    }

    return api_key


def validate_api_key(api_key: str = Depends(api_key_header)) -> Optional[Dict]:
    """
    Validate an API key.

    Args:
        api_key: The API key to validate

    Returns:
        Optional[Dict]: Key metadata if valid, None otherwise
    """
    if not api_key:
        return None

    key_data = API_KEYS.get(api_key)
    if not key_data:
        return None

    return key_data


def require_api_key(api_key: str = Depends(api_key_header)) -> Dict:
    """
    Require a valid API key.

    Args:
        api_key: The API key to validate

    Returns:
        Dict: Key metadata

    Raises:
        HTTPException: If API key is missing or invalid
    """
    key_data = validate_api_key(api_key)

    if not key_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "APIKey"},
        )

    return key_data


def sanitize_message(message: str) -> str:
    """
    Sanitize a message to remove potentially sensitive information.
    In aviation messaging, this is a placeholder but could be used to
    remove PII or other sensitive data before logging.

    Args:
        message: The message to sanitize

    Returns:
        str: The sanitized message
    """
    # This is a placeholder - implement actual sanitization if needed
    return message