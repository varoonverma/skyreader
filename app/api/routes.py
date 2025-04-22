# app/routes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.service.parser import parse_tty_message
from typing import List

router = APIRouter()

class ParseRequest(BaseModel):
    message: str
    message_id: str
    use_few_shots: bool = False

class ParseResponse(BaseModel):
    message_id: str
    parsed: dict

# Batch request/response models
class BatchParseRequest(BaseModel):
    message_list: List[ParseRequest]
    use_few_shots: bool = False

class BatchParseResponse(BaseModel):
    responses: List[ParseResponse]

@router.post("/parse", response_model=ParseResponse)
async def parse_endpoint(req: ParseRequest):
    try:
        parsed = parse_tty_message(req.message, req.use_few_shots)
    except Exception as e:
        # return a 502 Bad Gateway with the error text
        raise HTTPException(status_code=502, detail=str(e))
    return ParseResponse(message_id=req.message_id, parsed=parsed)



# Batch endpoint
@router.post("/parse/batch", response_model=BatchParseResponse)
async def parse_batch(req: BatchParseRequest):
    responses = []
    for item in req.message_list:
        try:
            parsed = parse_tty_message(item.message, req.use_few_shots)
        except Exception as e:
            raise HTTPException(status_code=502, detail=str(e))
        responses.append(ParseResponse(message_id=item.message_id, parsed=parsed))
    return BatchParseResponse(responses=responses)