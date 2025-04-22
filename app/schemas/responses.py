"""
Response schemas for the SkyReader TTY Message Parser.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.schemas.message import ParsedTTYMessage


class ParseResponse(BaseModel):
    """Response schema for TTY message parsing."""
    message_id: Optional[str] = Field(None, description="Message identifier if provided")
    parsed_data: ParsedTTYMessage = Field(..., description="Parsed TTY message data")
    parsing_method: str = Field("llm", description="Method used for parsing (llm or antlr)")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


class BatchParseResponse(BaseModel):
    """Response schema for batch TTY message parsing."""
    results: List[ParseResponse] = Field(..., description="List of parsing results")
    total_processing_time_ms: float = Field(..., description="Total processing time in milliseconds")
    successful_count: int = Field(..., description="Number of successfully parsed messages")
    failed_count: int = Field(..., description="Number of failed parses")
    summary: Dict[str, Any] = Field({}, description="Summary statistics of the batch processing")


class ErrorResponse(BaseModel):
    """Response schema for error cases."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: str = Field(..., description="Timestamp of the error")

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "error": "Failed to parse TTY message",
                "detail": "Invalid message format or missing required fields",
                "timestamp": "2025-04-22T15:30:45.123Z"
            }
        }


class HealthCheckResponse(BaseModel):
    """Response schema for health check endpoint."""
    status: str = Field(..., description="Service status (healthy/unhealthy)")
    version: str = Field(..., description="API version")
    model: str = Field(..., description="OpenAI model being used")
    uptime: float = Field(..., description="Service uptime in seconds")

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "0.1.0",
                "model": "gpt-4",
                "uptime": 3600.5
            }
        }


class ExampleResponse(BaseModel):
    """Response schema for example endpoint."""
    examples: List[ParseResponse] = Field(..., description="Example parsing results")
    count: int = Field(..., description="Number of examples")