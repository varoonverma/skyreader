"""
Dependencies for the SkyReader API.
"""
import time
from typing import Callable, Dict, List, Optional

from fastapi import Request, Response, Depends, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

from app.core.config import get_settings, Settings
from app.core.logging import get_logger


# Configure logger
logger = get_logger(__name__)

# API Key header (for future authentication)
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, limit: int = 10, window: int = 60):
        """
        Initialize the rate limiter.

        Args:
            limit: Maximum number of requests per window
            window: Time window in seconds
        """
        self.limit = limit
        self.window = window
        self.requests = {}  # {client_id: [(timestamp, count), ...]}

    def is_allowed(self, client_id: str) -> bool:
        """
        Check if a request is allowed based on rate limits.

        Args:
            client_id: Identifier for the client (IP address, API key, etc.)

        Returns:
            bool: True if request is allowed, False otherwise
        """
        now = time.time()

        # Initialize client if not seen before
        if client_id not in self.requests:
            self.requests[client_id] = [(now, 1)]
            return True

        # Clean up old requests outside the window
        self.requests[client_id] = [(ts, count) for ts, count in self.requests[client_id]
                                    if now - ts < self.window]

        # Count total requests in the window
        total_requests = sum(count for _, count in self.requests[client_id])

        # Check if limit is exceeded
        if total_requests >= self.limit:
            return False

        # Add new request
        if self.requests[client_id]:
            # Update the most recent timestamp
            latest = self.requests[client_id][-1]
            self.requests[client_id][-1] = (latest[0], latest[1] + 1)
        else:
            self.requests[client_id].append((now, 1))

        return True


# Initialize rate limiter
rate_limiter = RateLimiter()


async def get_api_key(
        api_key_header: str = Depends(API_KEY_HEADER),
        settings: Settings = Depends(get_settings)
) -> Optional[str]:
    """
    Get and validate API key from header.
    This is a placeholder for future authentication.

    Args:
        api_key_header: API key from header
        settings: Application settings

    Returns:
        Optional[str]: Validated API key or None
    """
    # Currently a placeholder - no actual API key validation
    return api_key_header


async def verify_rate_limit(request: Request, settings: Settings = Depends(get_settings)):
    """
    Verify rate limit for the current client.

    Args:
        request: FastAPI request object
        settings: Application settings

    Raises:
        HTTPException: If rate limit is exceeded
    """
    # Get client identifier (IP address for now)
    client_id = request.client.host if request.client else "unknown"

    # Check if request is allowed
    if not rate_limiter.is_allowed(client_id):
        logger.warning(f"Rate limit exceeded for client: {client_id}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )


async def log_request_timing(request: Request, call_next: Callable) -> Response:
    """
    Middleware to log request timing.

    Args:
        request: FastAPI request object
        call_next: Next middleware function

    Returns:
        Response: The response from the next middleware
    """
    start_time = time.time()

    # Process the request
    response = await call_next(request)

    # Calculate processing time
    process_time = time.time() - start_time

    # Add timing header
    response.headers["X-Process-Time"] = str(process_time)

    # Log request timing
    logger.debug(
        f"Request {request.method} {request.url.path} processed in {process_time:.4f} seconds"
    )

    return response