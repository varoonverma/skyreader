"""
Pytest configuration for the SkyReader tests.
"""
import os
import pytest
from typing import Dict, Any

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.message import FlightIdentifier, ParsedTTYMessage


@pytest.fixture
def test_client():
    """
    Create a test client for FastAPI app.

    Returns:
        TestClient: FastAPI test client
    """
    return TestClient(app)


@pytest.fixture
def sample_tty_message() -> str:
    """
    Sample TTY message for testing.

    Returns:
        str: Sample TTY message
    """
    return """QU HDQWWQF
.TDY9999 060154
A81
FI QFA8666/AN VH-ZNM
DT TDY TDY 060154 M43A
-
MVA
QFA8666/09.VHZNM.YPGV
AA0745/0753"""


@pytest.fixture
def mva_message() -> str:
    """
    Sample MVA TTY message for testing.

    Returns:
        str: Sample MVA TTY message
    """
    return """QU HDQWWQF
.TDY9999 060154
A81
FI QFA8666/AN VH-ZNM
DT TDY TDY 060154 M43A
-
MVA
QFA8666/09.VHZNM.YPGV
AA0745/0753"""


@pytest.fixture
def mvt_message() -> str:
    """
    Sample MVT TTY message for testing.

    Returns:
        str: Sample MVT TTY message
    """
    return """QU HDQWWQF
.TDY9999 090154
A81
FI QFA4994/AN VH-XVN
DT TDY TDY 060154 M43A
-
MVT
QFA4994/.VHXVN.NZDN
AD0820/0835"""


@pytest.fixture
def div_message() -> str:
    """
    Sample DIV TTY message for testing.

    Returns:
        str: Sample DIV TTY message
    """
    return """QU HDQWWQF
.TDY9999 090154
A81
FI QFA4994/AN VH-XVN
DT TDY TDY 060154 M43A
-
DIV
QFA4994/.VHXVN.NZDN
EA2135 LHR
DR71
PX112"""


@pytest.fixture
def sample_parsed_message(sample_tty_message) -> ParsedTTYMessage:
    """
    Sample parsed TTY message for testing.

    Returns:
        ParsedTTYMessage: Sample parsed TTY message
    """
    return ParsedTTYMessage(
        message_type="MVA",
        flight_identifier=FlightIdentifier(
            designator="QFA",
            flight_number="8666",
            scheduled_date="09"
        ),
        aircraft_registration="VHZNM",
        airport_of_movement="YPGV",
        message_specific_data={"arrival_time": "0745/0753"},
        supplementary_info=None,
        raw_message=sample_tty_message,
        confidence_score=0.95
    )


@pytest.fixture
def mock_env():
    """
    Mock environment variables for testing.

    Yields:
        Dict[str, str]: Dictionary of mock environment variables
    """
    original_env = os.environ.copy()

    # Set test environment variables
    os.environ["OPENAI_API_KEY"] = "test-api-key"
    os.environ["OPENAI_MODEL"] = "gpt-4"
    os.environ["OPENAI_TEMPERATURE"] = "0.0"
    os.environ["OPENAI_MAX_TOKENS"] = "1000"
    os.environ["CONFIDENCE_THRESHOLD"] = "0.8"
    os.environ["FALLBACK_TO_ANTLR"] = "false"
    os.environ["BATCH_SIZE"] = "10"
    os.environ["REQUEST_TIMEOUT"] = "30"

    yield os.environ

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def openai_mock_response() -> Dict[str, Any]:
    """
    Mock OpenAI API response for testing.

    Returns:
        Dict[str, Any]: Mock OpenAI API response
    """
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677858242,
        "model": "gpt-4",
        "usage": {
            "prompt_tokens": 57,
            "completion_tokens": 88,
            "total_tokens": 145
        },
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": """
                    {
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
                      "supplementary_info": null
                    }
                    """
                },
                "finish_reason": "stop",
                "index": 0
            }
        ]
    }