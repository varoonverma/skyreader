"""
Message schemas for the SkyReader TTY Message Parser.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field




class TTYMessageRequest(BaseModel):
    """Request schema for TTY message parsing."""
    message: str = Field(..., description="Raw TTY message to parse")
    message_id: Optional[str] = Field(None, description="Optional message identifier")
    use_few_shot: Optional[bool] = Field(True, description="Whether to use few-shot examples")

class FlightIdentificationMessage(BaseModel):
    """Schema for flight identification message."""
    airline_iata: str
    flight_number: str
    registration: str

class FlightIdentifier(BaseModel):
    """Schema for flight identifier information."""
    airline_iata: str
    flight_number: str
    registration: str
    movement_day: Optional[str] = None

class MovementInfo(BaseModel):
    """Schema for movement information."""
    type: str
    movement: str
    blocks_off_time: Optional[str] = None
    wheels_off_time: Optional[str] = None
    blocks_on_time: Optional[str] = None
    wheels_on_time: Optional[str] = None
    estimated_arrival_time: Optional[str] = None
    departure_airport_iata: Optional[str] = None
    arrival_airport_iata: Optional[str] = None

class ParsedTTYMessage(BaseModel):
    """Schema for parsed TTY message."""
    priority_code: str
    destination_address: List[str]
    origin_address: str
    message_identify: str
    report_indicator: str
    flight_identification_message: FlightIdentificationMessage
    communication_service_information: str
    standard_message_id: str
    flight_identifier: FlightIdentifier
    movement_info: MovementInfo
    supplementary_info: Optional[str] = None
    raw_message: str = Field(..., description="Original raw TTY message")
    confidence_score: Optional[float] = Field(None, description="Confidence score of parsing")

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "message_type": "MVA",
                "flight_identifier": {
                    "designator": "QFA",
                    "flight_number": "8666",
                    "scheduled_date": "09"
                },
                "aircraft_registration": "VHZNM",
                "airport_of_movement": "YPGV",
                "message_specific_data": {
                    "arrival_time": "0745/0753"
                },
                "supplementary_info": None,
                "raw_message": "QU HDQWWQF\n.TDY9999 060154\nA81\nFI QFA8666/AN VH-ZNM\nDT TDY TDY 060154 M43A\n-\nMVA\nQFA8666/09.VHZNM.YPGV\nAA0745/0753",
                "confidence_score": 0.95
            }
        }


class BatchTTYMessageRequest(BaseModel):
    """Request schema for batch TTY message parsing."""
    messages: List[TTYMessageRequest] = Field(..., description="List of TTY messages to parse")


class MVAMessageData(BaseModel):
    """Schema for MVA (Movement Arrival) message specific data."""
    arrival_time: Optional[str] = Field(None, description="Aircraft arrival time (touchdown/on-block)")
    estimated_arrival_time: Optional[str] = Field(None, description="Estimated arrival time")
    estimated_onblock_time: Optional[str] = Field(None, description="Estimated on-block time")
    delay_codes: Optional[List[Dict[str, str]]] = Field(None, description="Delay reason codes")


class MVTMessageData(BaseModel):
    """Schema for MVT (Movement) message specific data."""
    departure_time: Optional[str] = Field(None, description="Aircraft departure time (off-block/airborne)")
    estimated_departure_time: Optional[str] = Field(None, description="Estimated departure time")
    estimated_takeoff_time: Optional[str] = Field(None, description="Estimated take-off time")
    delay_codes: Optional[List[Dict[str, str]]] = Field(None, description="Delay reason codes")
    passenger_info: Optional[str] = Field(None, description="Passenger information")


class DIVMessageData(BaseModel):
    """Schema for DIV (Diversion) message specific data."""
    diversion_airport: str = Field(..., description="Airport the flight was diverted to")
    diversion_reason_code: Optional[str] = Field(None, description="Reason code for diversion")
    estimated_arrival_time: Optional[str] = Field(None, description="Estimated arrival time at diversion airport")
    passenger_count: Optional[int] = Field(None, description="Number of passengers on board")