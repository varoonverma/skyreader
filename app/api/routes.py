from typing import List

from fastapi import APIRouter
from pydantic import BaseModel, Field
import asyncio
import logging
from app.parser.parser import ParserService
from app.parser.remote import RemoteModelParser
from app.parser.local import LocalModelParser
from app.exceptions import ParserConfigError

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
    use_few_shots: bool = Field(
        default=False,
        description="Use few-shot examples for local model"
    )


class ParseResponse(BaseModel):
    message_id: str
    parsed: dict


class BatchParseRequest(BaseModel):
    items: List[ParseRequest]


class BatchParseResponse(BaseModel):
    responses: List[ParseResponse]

def make_parser(model: str, compact: bool, use_few_shots: bool = False) -> ParserService:
    """Factory function to create an appropriate parser based on model type"""
    if model == "openai":
        return ParserService(RemoteModelParser(model="openai"), compact=compact)
    elif model == "tuned_openai":
        return ParserService(RemoteModelParser(model="tuned_openai"), compact=compact)
    elif model == "local":
        return ParserService(LocalModelParser(use_few_shots=use_few_shots), compact=compact)
    else:
        raise ParserConfigError(f"Unknown model type: {model}")

@router.post("/parse", response_model=ParseResponse)
async def parse_endpoint(req: ParseRequest):
    """Parse a single TTY message"""
    try:
        # Configure parser based on request
        parser = make_parser(req.model, compact=req.compact, use_few_shots=req.use_few_shots)

        # Parse the message
        result = parser.parse_tty_message(req.message)

        return ParseResponse(message_id=req.message_id, parsed=result)
    except Exception as e:
        logging.error(f"Error processing message {req.message_id}: {str(e)}", exc_info=True)
        raise

@router.post("/parse/batch", response_model=BatchParseResponse)
async def parse_batch(req: BatchParseRequest):
    """Process multiple messages concurrently"""
    # Create tasks for each message
    tasks = [parse_message_async(item) for item in req.items]

    # Execute all tasks concurrently
    responses = await asyncio.gather(*tasks)

    return BatchParseResponse(responses=responses)

async def parse_message_async(req: ParseRequest) -> ParseResponse:
    """Process a single message asynchronously"""
    try:
        parser = make_parser(req.model, compact=req.compact, use_few_shots=req.use_few_shots)
        result = parser.parse_tty_message(req.message)
        return ParseResponse(message_id=req.message_id, parsed=result)
    except Exception as e:
        logging.error(f"Error processing message {req.message_id}: {str(e)}")
        return ParseResponse(message_id=req.message_id, parsed={"error": str(e)})