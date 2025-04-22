"""
Message validation utilities for the SkyReader TTY Message Parser.
"""
import re
from typing import Optional, Tuple, Dict, Any

from app.core.logging import get_logger

logger = get_logger(__name__)


def validate_tty_message(message: str) -> bool:
    """
    Perform basic validation on a TTY message format.

    Args:
        message: The raw TTY message to validate

    Returns:
        bool: True if the message appears to be a valid TTY message, False otherwise
    """
    # Check if message is empty or too short
    if not message or len(message) < 10:
        logger.warning("Message validation failed: message too short")
        return False

    # Check for typical TTY message header patterns
    header_pattern = r"QU\s+\w+"
    if not re.search(header_pattern, message):
        logger.warning("Message validation failed: missing QU header")
        return False

    # Check for message type indicators
    message_type_pattern = r"(MVT|MVA|DIV)"
    if not re.search(message_type_pattern, message):
        logger.warning("Message validation failed: missing message type (MVT/MVA/DIV)")
        return False

    # Check for flight identifier pattern (e.g., QFA8666)
    flight_pattern = r"([A-Z]{2,3})(\d{1,4})"
    if not re.search(flight_pattern, message):
        logger.warning("Message validation failed: missing flight identifier")
        return False

    return True


def detect_message_type(message: str) -> Optional[str]:
    """
    Detect the type of TTY message (MVT, MVA, DIV).

    Args:
        message: The raw TTY message

    Returns:
        Optional[str]: The detected message type, or None if not detected
    """
    # Check for explicit message type indicators
    pattern = r"(MVT|MVA|DIV)"
    match = re.search(pattern, message)
    if match:
        return match.group(0)

    # If no explicit indicator, try to infer from content patterns
    if re.search(r"AA\d{4}", message):
        # AA followed by 4 digits typically indicates an arrival message
        return "MVA"
    elif re.search(r"AD\d{4}", message):
        # AD followed by 4 digits typically indicates a departure message
        return "MVT"
    elif re.search(r"EA\d{4}\s+[A-Z]{3}", message):
        # EA followed by 4 digits and an airport code typically indicates a diversion
        return "DIV"

    # Couldn't detect message type
    return None


def extract_basic_fields(message: str) -> Dict[str, Any]:
    """
    Extract basic fields from a TTY message using regex patterns.
    This is a fallback method for basic extraction when full parsing fails.

    Args:
        message: The raw TTY message

    Returns:
        Dict[str, Any]: Basic fields extracted from the message
    """
    fields = {}

    # Extract message type
    message_type = detect_message_type(message)
    if message_type:
        fields["message_type"] = message_type

    # Extract flight number (e.g., QFA8666)
    flight_match = re.search(r"([A-Z]{2,3})(\d{1,4})", message)
    if flight_match:
        fields["flight_identifier"] = {
            "designator": flight_match.group(1),
            "flight_number": flight_match.group(2),
            "scheduled_date": None
        }

        # Try to extract scheduled date if it's in the common format
        date_match = re.search(r"([A-Z]{2,3}\d{1,4})/(\d{1,2})", message)
        if date_match and date_match.group(1) == f"{flight_match.group(1)}{flight_match.group(2)}":
            fields["flight_identifier"]["scheduled_date"] = date_match.group(2)

    # Extract aircraft registration (e.g., .VHZNM or VH-ZNM)
    reg_match = re.search(r"\.([A-Z0-9-]{4,8})", message) or re.search(r"AN\s+([A-Z0-9-]{4,8})", message)
    if reg_match:
        fields["aircraft_registration"] = reg_match.group(1)

    # Extract airport code (typically 3 or 4 letter code after a period)
    airport_match = re.search(r"\.([A-Z]{3,4})\b", message)
    if airport_match:
        fields["airport_of_movement"] = airport_match.group(1)

    # Extract message specific data based on message type
    if message_type == "MVA":
        # Look for arrival time (AA followed by digits)
        arr_match = re.search(r"AA(\d{4})(?:/(\d{4}))?", message)
        if arr_match:
            if arr_match.group(2):
                fields["message_specific_data"] = {"arrival_time": f"{arr_match.group(1)}/{arr_match.group(2)}"}
            else:
                fields["message_specific_data"] = {"arrival_time": arr_match.group(1)}

    elif message_type == "MVT":
        # Look for departure time (AD followed by digits)
        dep_match = re.search(r"AD(\d{4})(?:/(\d{4}))?", message)
        if dep_match:
            if dep_match.group(2):
                fields["message_specific_data"] = {"departure_time": f"{dep_match.group(1)}/{dep_match.group(2)}"}
            else:
                fields["message_specific_data"] = {"departure_time": dep_match.group(1)}

    elif message_type == "DIV":
        # Look for diversion airport and reason
        div_match = re.search(r"EA\d{4}\s+([A-Z]{3})", message)
        reason_match = re.search(r"DR(\d{2})", message)

        fields["message_specific_data"] = {}

        if div_match:
            fields["message_specific_data"]["diversion_airport"] = div_match.group(1)

        if reason_match:
            fields["message_specific_data"]["diversion_reason_code"] = reason_match.group(1)

    else:
        # Default empty message specific data
        fields["message_specific_data"] = {}

    # Include the raw message
    fields["raw_message"] = message

    return fields


def validate_parsed_fields(parsed_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate that the parsed fields contain all required information.

    Args:
        parsed_data: The parsed TTY message data

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    # Check required fields
    required_fields = ["message_type", "flight_identifier", "aircraft_registration",
                       "airport_of_movement", "message_specific_data"]

    for field in required_fields:
        if field not in parsed_data:
            return False, f"Missing required field: {field}"

    # Check flight identifier structure
    flight_id = parsed_data.get("flight_identifier", {})
    if not isinstance(flight_id, dict):
        return False, "Flight identifier must be an object"

    if "designator" not in flight_id or "flight_number" not in flight_id:
        return False, "Flight identifier missing designator or flight_number"

    # Check message type is valid
    if parsed_data["message_type"] not in ["MVT", "MVA", "DIV"]:
        return False, f"Invalid message type: {parsed_data['message_type']}"

    # Check message specific data based on message type
    msg_data = parsed_data.get("message_specific_data", {})
    if parsed_data["message_type"] == "MVA" and not any(k in msg_data for k in ["arrival_time", "estimated_arrival_time"]):
        return False, "MVA message missing arrival information"

    if parsed_data["message_type"] == "MVT" and not any(k in msg_data for k in ["departure_time", "estimated_departure_time"]):
        return False, "MVT message missing departure information"

    if parsed_data["message_type"] == "DIV" and "diversion_airport" not in msg_data:
        return False, "DIV message missing diversion airport"

    return True, None