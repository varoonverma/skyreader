from typing import List

from fastapi import APIRouter
from pydantic import BaseModel, Field
import asyncio
import logging
from app.service.parser import ParserService
from app.service.remote_parser import RemoteModelParser

router = APIRouter()


class ParseRequest(BaseModel):
    message: str = Field(..., description="Raw TTY message to parse")
    message_id: str = Field(..., description="Client-provided message ID")
    model: str = Field(
        default="openai",
        description="Parser identifier"
    )
    compact: bool = Field(
        default=True,
        description="If True return only parsed JSON, else full response dict"
    )


class ParseResponse(BaseModel):
    message_id: str
    parsed: dict


class BatchParseRequest(BaseModel):
    items: List[ParseRequest]


class BatchParseResponse(BaseModel):
    responses: List[ParseResponse]

def make_parser(model: str, compact: bool) -> ParserService:
    return ParserService(RemoteModelParser(model=model), compact=compact)

@router.post("/parse", response_model=ParseResponse)
async def parse_message_async(req: ParseRequest) -> ParseResponse:
    """Process a single message asynchronously"""
    parser = make_parser(req.model, compact=req.compact)
    result = parser.parse_tty_message(req.message)
    return ParseResponse(message_id=req.message_id, parsed=result)

@router.post("/parse/batch", response_model=BatchParseResponse)
async def parse_batch(req: BatchParseRequest):
    """Process multiple messages concurrently"""
    # Create tasks for each message
    tasks = [parse_message_async(item) for item in req.items]

    # Execute all tasks concurrently
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle any exceptions that occurred
    processed_responses = []
    for i, response in enumerate(responses):
        if isinstance(response, Exception):
            # Log the error
            logging.error(f"Error processing message {req.items[i].message_id}: {str(response)}")
            # Create an error response
            processed_responses.append(
                ParseResponse(
                    message_id=req.items[i].message_id,
                    parsed={"error": str(response)}
                )
            )
        else:
            processed_responses.append(response)

    return BatchParseResponse(responses=processed_responses)