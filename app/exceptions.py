# app/exceptions.py
from typing import Dict, Any, Optional


class SkyReaderError(Exception):
    """Base exception for SkyReader app"""
    status_code: int = 500
    detail: str = "An error occurred"

    def __init__(self, detail: Optional[str] = None):
        self.detail = detail or self.detail
        super().__init__(self.detail)

    def to_dict(self) -> Dict[str, Any]:
        return {"detail": self.detail}


class ParserConfigError(SkyReaderError):
    """Raised when parser configuration is invalid"""
    status_code: int = 400
    detail: str = "Invalid parser configuration"


class RemoteModelError(SkyReaderError):
    """Raised when there's an error with the remote model"""
    status_code: int = 502
    detail: str = "Error communicating with remote model"


class ParseError(SkyReaderError):
    """Raised when parsing fails"""
    status_code: int = 422
    detail: str = "Failed to parse message"