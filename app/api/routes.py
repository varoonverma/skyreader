from typing import List

from fastapi import APIRouter
from pydantic import BaseModel, Field

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
async def parse_endpoint(req: ParseRequest):
    # 1) configure a fresh RemoteModelParser & ParserService per call
    parser = make_parser(req.model, compact=req.compact)

    result = parser.parse_tty_message(req.message)

    return ParseResponse(message_id=req.message_id, parsed=result)

@router.post("/parse/batch", response_model=BatchParseResponse)
async def parse_batch(req: BatchParseRequest):
    responses: List[ParseResponse] = []

    for req in req.items:
        parser = make_parser(req.model, compact=req.compact)

        result = parser.parse_tty_message(req.message)

        responses.append(ParseResponse(message_id=req.message_id, parsed=result))

    return BatchParseResponse(responses=responses)