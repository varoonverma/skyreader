"""
Tests for the SkyReader API routes.
"""
import json
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.message import FlightIdentifier, ParsedTTYMessage


# Create test client
client = TestClient(app)

# Sample TTY message for testing
SAMPLE_TTY_MESSAGE = """QU HDQWWQF
.TDY9999 060154
A81
FI QFA8666/AN VH-ZNM
DT TDY TDY 060154 M43A
-
MVA
QFA8666/09.VHZNM.YPGV
AA0745/0753"""

# Sample parsed message for mocking
SAMPLE_PARSED_MESSAGE = ParsedTTYMessage(
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
    raw_message=SAMPLE_TTY_MESSAGE,
    confidence_score=0.95
)


def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome to" in response.json()["message"]
    assert "version" in response.json()


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert "version" in response.json()
    assert "model" in response.json()
    assert "uptime" in response.json()


@patch("app.api.routes.parse_tty_message")
def test_parse_endpoint_success(mock_parse):
    """Test the parse endpoint with successful parsing."""
    # Mock the parser function
    mock_parse.return_value = (SAMPLE_PARSED_MESSAGE, 123.45, "llm")

    # Make the request
    response = client.post(
        "/parse",
        json={"message": SAMPLE_TTY_MESSAGE, "message_id": "test-1"}
    )

    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert data["message_id"] == "test-1"
    assert data["parsing_method"] == "llm"
    assert data["processing_time_ms"] == 123.45
    assert data["parsed_data"]["message_type"] == "MVA"
    assert data["parsed_data"]["flight_identifier"]["designator"] == "QFA"

    # Verify the mock was called correctly
    mock_parse.assert_called_once_with(SAMPLE_TTY_MESSAGE, "test-1")


@patch("app.api.routes.parse_tty_message")
def test_parse_endpoint_invalid_message(mock_parse):
    """Test the parse endpoint with an invalid message."""
    # Mock the parser function to raise an error
    mock_parse.side_effect = ValueError("Invalid TTY message format")

    # Make the request
    response = client.post(
        "/parse",
        json={"message": "invalid message", "message_id": "test-2"}
    )

    # Check the response
    assert response.status_code == 400
    assert "error" in response.json()
    assert "Failed to parse TTY message" in response.json()["error"]


@patch("app.api.routes.batch_parse_tty_messages")
def test_batch_parse_endpoint_success(mock_batch_parse):
    """Test the batch parse endpoint with successful parsing."""
    # Mock the batch parser function
    mock_batch_parse.return_value = [
        (SAMPLE_PARSED_MESSAGE, 123.45, "llm", "test-1"),
        (SAMPLE_PARSED_MESSAGE, 234.56, "llm", "test-2")
    ]

    # Make the request
    response = client.post(
        "/batch_parse",
        json={
            "messages": [
                {"message": SAMPLE_TTY_MESSAGE, "message_id": "test-1"},
                {"message": SAMPLE_TTY_MESSAGE, "message_id": "test-2"}
            ]
        }
    )

    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert data["successful_count"] == 2
    assert data["failed_count"] == 0
    assert len(data["results"]) == 2
    assert data["results"][0]["message_id"] == "test-1"
    assert data["results"][1]["message_id"] == "test-2"

    # Verify the mock was called correctly
    mock_batch_parse.assert_called_once()
    # Check that it was called with the correct arguments
    call_args = mock_batch_parse.call_args[0][0]
    assert len(call_args) == 2
    assert call_args[0][0] == SAMPLE_TTY_MESSAGE
    assert call_args[0][1] == "test-1"
    assert call_args[1][0] == SAMPLE_TTY_MESSAGE
    assert call_args[1][1] == "test-2"


@patch("app.api.routes.batch_parse_tty_messages")
def test_batch_parse_endpoint_too_many_messages(mock_batch_parse):
    """Test the batch parse endpoint with too many messages."""
    # Create a large batch of messages
    large_batch = [{"message": SAMPLE_TTY_MESSAGE, "message_id": f"test-{i}"} for i in range(100)]

    # Make the request
    response = client.post(
        "/batch_parse",
        json={"messages": large_batch}
    )

    # Check the response
    assert response.status_code == 400
    assert "error" in response.json()
    assert "Batch size exceeded" in response.json()["error"]

    # Verify the mock was not called
    mock_batch_parse.assert_not_called()


@patch("app.api.routes.parse_tty_message")
def test_examples_endpoint(mock_parse):
    """Test the examples endpoint."""
    # Mock the parser function
    mock_parse.return_value = (SAMPLE_PARSED_MESSAGE, 123.45, "llm")

    # Make the request
    response = client.get("/examples")

    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert "examples" in data
    assert "count" in data
    assert len(data["examples"]) > 0

    # Verify the mock was called (at least once)
    assert mock_parse.call_count > 0