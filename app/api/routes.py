"""
API routes for the SkyReader TTY Message Parser.
"""
import time
import datetime
from typing import List

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse

from app.core.config import get_settings, Settings
from app.core.logging import get_logger, log_request_info
from app.schemas.message import TTYMessageRequest, BatchTTYMessageRequest
from app.schemas.responses import (
    ParseResponse,
    BatchParseResponse,
    ErrorResponse,
    HealthCheckResponse,
    ExampleResponse
)
from app.services.parser_service import parse_tty_message, batch_parse_tty_messages
from app.utils.message_validator import validate_tty_message

# Configure logger
logger = get_logger(__name__)

# Create router
router = APIRouter()

# Store the application start time for uptime reporting
start_time = time.time()

# Sample TTY messages for examples
SAMPLE_MESSAGES = [
    {
        "message": """QU HDQWWQF
.TDY9999 060154
A81
FI QFA8666/AN VH-ZNM
DT TDY TDY 060154 M43A
-
MVA
QFA8666/09.VHZNM.YPGV
AA0745/0753""",
        "message_id": "example-1"
    },
    {
        "message": """QU HDQWWQF
.TDY9999 090154
A81
FI QFA4994/AN VH-XVN
DT TDY TDY 060154 M43A
-
MVA
QFA4994/.VHXVN.NZDN
AD0820/0835""",
        "message_id": "example-2"
    }
]


@router.get("/", summary="Root endpoint", tags=["General"])
async def root(settings: Settings = Depends(get_settings)):
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "documentation": "/docs"
    }


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health check",
    tags=["General"]
)
async def health_check(settings: Settings = Depends(get_settings)):
    """
    Health check endpoint.
    Returns the current status of the API.
    """
    uptime = time.time() - start_time

    return HealthCheckResponse(
        status="healthy",
        version=settings.app_version,
        model=settings.openai_model,
        uptime=uptime
    )


@router.post(
    "/parse",
    response_model=ParseResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Parse a single TTY message",
    tags=["Parsing"]
)
async def parse_message(
        request: TTYMessageRequest,
        settings: Settings = Depends(get_settings)
):
    """
    Parse a single TTY message.

    Returns the structured data extracted from the TTY message.
    """
    # Log the request
    log_request_info(request.dict(), logger)

    # Validate message format
    if not validate_tty_message(request.message):
        error_response = ErrorResponse(
            error="Invalid TTY message format",
            detail="The message does not match the expected TTY message format",
            timestamp=datetime.datetime.now().isoformat()
        )
        return JSONResponse(
            status_code=400,
            content=error_response.dict()
        )

    try:
        # Parse the message
        parsed_message, processing_time, parsing_method = parse_tty_message(
            request.message, request.message_id, request.use_few_shot
        )

        # Create response
        response = ParseResponse(
            message_id=request.message_id,
            parsed_data=parsed_message,
            parsing_method=parsing_method,
            processing_time_ms=processing_time
        )

        return response

    except ValueError as e:
        error_response = ErrorResponse(
            error="Failed to parse TTY message",
            detail=str(e),
            timestamp=datetime.datetime.now().isoformat()
        )
        return JSONResponse(
            status_code=400,
            content=error_response.dict()
        )

    except Exception as e:
        logger.exception(f"Unexpected error parsing message {request.message_id}: {str(e)}")

        error_response = ErrorResponse(
            error="Internal server error",
            detail=f"Error parsing message: {str(e)}",
            timestamp=datetime.datetime.now().isoformat()
        )
        return JSONResponse(
            status_code=500,
            content=error_response.dict()
        )


@router.post(
    "/batch_parse",
    response_model=BatchParseResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Parse multiple TTY messages in batch",
    tags=["Parsing"]
)
async def batch_parse(
        request: BatchTTYMessageRequest,
        background_tasks: BackgroundTasks,
        settings: Settings = Depends(get_settings)
):
    """
    Parse multiple TTY messages in a batch.

    Returns the structured data extracted from each TTY message.
    """
    start_time = time.time()
    results = []
    failed_count = 0

    # Log batch size
    logger.info(f"Processing batch of {len(request.messages)} messages")

    # Prepare messages for batch processing
    message_pairs = [(msg.message, msg.message_id) for msg in request.messages]

    # Impose a maximum batch size for API calls
    max_batch_size = min(settings.batch_size, 50)  # Limit to 50 messages max per request

    if len(message_pairs) > max_batch_size:
        error_response = ErrorResponse(
            error="Batch size exceeded",
            detail=f"Maximum batch size is {max_batch_size}, received {len(message_pairs)}",
            timestamp=datetime.datetime.now().isoformat()
        )
        return JSONResponse(
            status_code=400,
            content=error_response.dict()
        )

    try:
        # Process the batch
        batch_results = batch_parse_tty_messages(message_pairs)
        results.extend(batch_results)

        # Calculate failed count
        failed_count = len(message_pairs) - len(batch_results)

    except Exception as e:
        logger.exception(f"Batch processing error: {str(e)}")

        error_response = ErrorResponse(
            error="Batch processing error",
            detail=str(e),
            timestamp=datetime.datetime.now().isoformat()
        )
        return JSONResponse(
            status_code=500,
            content=error_response.dict()
        )

    # Calculate total processing time
    total_processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds

    # Create response objects
    parse_responses = [
        ParseResponse(
            message_id=message_id,
            parsed_data=parsed_data,
            parsing_method=method,
            processing_time_ms=proc_time
        )
        for parsed_data, proc_time, method, message_id in results
    ]

    # Calculate summary statistics
    methods_used = {}
    avg_confidence = 0.0

    for parsed_data, _, method, _ in results:
        methods_used[method] = methods_used.get(method, 0) + 1
        avg_confidence += parsed_data.confidence_score or 0.0

    if results:
        avg_confidence /= len(results)

    summary = {
        "methods_used": methods_used,
        "average_confidence": avg_confidence,
        "average_time_ms": total_processing_time / len(message_pairs) if message_pairs else 0
    }

    # Create batch response
    response = BatchParseResponse(
        results=parse_responses,
        total_processing_time_ms=total_processing_time,
        successful_count=len(results),
        failed_count=failed_count,
        summary=summary
    )

    # Add background task to log statistics
    background_tasks.add_task(logger.info, f"Batch processing summary: {summary}")

    return response


@router.get(
    "/examples",
    response_model=ExampleResponse,
    summary="Get example parsed TTY messages",
    tags=["Examples"]
)
async def get_examples():
    """
    Get example parsed TTY messages.

    Returns pre-parsed examples of TTY messages to demonstrate the API.
    """
    examples = []

    for sample in SAMPLE_MESSAGES:
        try:
            parsed_message, processing_time, parsing_method = parse_tty_message(
                sample["message"], sample["message_id"]
            )

            response = ParseResponse(
                message_id=sample["message_id"],
                parsed_data=parsed_message,
                parsing_method=parsing_method,
                processing_time_ms=processing_time
            )

            examples.append(response)
        except Exception as e:
            logger.error(f"Error processing example: {str(e)}")
            # Skip failed examples
            continue

    return ExampleResponse(
        examples=examples,
        count=len(examples)
    )