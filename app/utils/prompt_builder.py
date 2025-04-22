"""
LLM prompt building utilities for the SkyReader TTY Message Parser.
"""
from typing import Dict, Any, Optional, List
import json


def create_parsing_prompt(tty_message: str, message_type: Optional[str] = None) -> str:
    """
    Create an optimized prompt for the LLM to parse a TTY message.

    Args:
        tty_message: The raw TTY message to parse
        message_type: Optional hint about the message type (MVT, MVA, DIV)

    Returns:
        str: The formatted prompt for the LLM
    """
    type_hint = ""
    if message_type:
        type_hint = f"\nNote: This appears to be a {message_type} message."

    prompt = f"""
    You are SkyReader, a specialized parser for aviation TTY messages used by Qantas airline. 
    Convert the following TTY message into structured data according to the MVT/MVA/DIV message format guidelines.
    
    MESSAGE TO PARSE:
    ```
    {tty_message}
    ```{type_hint}
    
    TTY messages follow this structure:
    - They begin with headers (QU, priority codes, etc.)
    - They contain a message type (MVT, MVA, or DIV)
    - They include flight identifiers (e.g., QFA8666/09)
    - They include aircraft registration (e.g., .VHZNM)
    - They include airport codes (e.g., .YPGV)
    - They may contain timing information like arrivals (AA0745/0753) or departures
    - They may contain supplementary information
    
    Message type specific information:
    - MVA (Movement Arrival) messages include arrival information with AA prefix
    - MVT (Movement) messages include departure information with AD prefix
    - DIV (Diversion) messages include information about flight diversions
    
    Extract all fields and return ONLY a valid JSON object with the following structure:
    {{
      "message_type": "MVT" or "MVA" or "DIV",
      "flight_identifier": {{
        "designator": "QFA", 
        "flight_number": "8666", 
        "scheduled_date": "09"
      }},
      "aircraft_registration": "VHZNM",
      "airport_of_movement": "YPGV",
      "message_specific_data": {{
        // Include all message-specific fields here based on message type
        // For MVA messages, include arrival information
        // For MVT messages, include departure information
        // For DIV messages, include diversion information
      }},
      "supplementary_info": ""
    }}
    
    IMPORTANT: Your response must be ONLY the JSON object, nothing else. Ensure it's valid JSON.
    """
    return prompt


def create_detailed_parsing_prompt(tty_message: str, message_type: Optional[str] = None) -> str:
    """
    Create a more detailed prompt for difficult cases or high accuracy needs.

    Args:
        tty_message: The raw TTY message to parse
        message_type: Optional hint about the message type (MVT, MVA, DIV)

    Returns:
        str: The formatted detailed prompt for the LLM
    """
    base_prompt = create_parsing_prompt(tty_message, message_type)

    additional_guidance = f"""
    Also consider these details for specific fields:
    
    For MVA (Movement Arrival) messages:
    - Look for "AA" followed by four or more digits, often indicating arrival time
    - The format is often AA[time]/[time] for touchdown/on-block times
    - Examples: AA0745/0753, AA1215
    
    For MVT (Movement) messages:
    - Look for "AD" followed by four or more digits, often indicating departure time
    - The format is often AD[time]/[time] for off-block/airborne times
    - Look for "DL" followed by codes like "DL72/0015" for delay information
    - Examples: AD0820/0835, DL72/0015
    
    For DIV (Diversion) messages:
    - Look for "EA" followed by time and airport code for estimated arrival at diversion
    - Look for "DR" followed by a numeric code for diversion reason
    - Examples: EA2135 LHR, DR71
    
    Aircraft registration:
    - Look for a period followed by 5-7 characters, like ".VHZNM"
    - Some messages format it with the flight number, like "QFA8666/09.VHZNM.YPGV"
    
    Make sure to handle all cases carefully and return the structured data.
    """

    return base_prompt + additional_guidance


def create_batch_processing_prompt(tty_messages: list[str]) -> str:
    """
    Create a prompt for batch processing multiple TTY messages.

    Args:
        tty_messages: List of raw TTY messages to parse

    Returns:
        str: The formatted prompt for batch processing
    """
    messages_text = "\n\n".join([f"Message {i+1}:\n```\n{msg}\n```" for i, msg in enumerate(tty_messages)])

    prompt = f"""
    You are SkyReader, a specialized parser for aviation TTY messages used by Qantas airline.
    Parse the following batch of TTY messages into structured data according to the MVT/MVA/DIV message format guidelines.
    
    MESSAGES TO PARSE:
    
    {messages_text}
    
    For each message, extract all relevant fields and return an array of JSON objects with the following structure for each message:
    {{
      "message_number": 1,
      "message_type": "MVT" or "MVA" or "DIV",
      "flight_identifier": {{
        "designator": "QFA", 
        "flight_number": "8666", 
        "scheduled_date": "09"
      }},
      "aircraft_registration": "VHZNM",
      "airport_of_movement": "YPGV",
      "message_specific_data": {{
        // Include all message-specific fields here based on message type
      }},
      "supplementary_info": ""
    }}
    
    IMPORTANT: Your response must be ONLY a JSON array containing one object per message, nothing else. Ensure it's valid JSON.
    """
    return prompt


def create_fallback_prompt(tty_message: str, error_details: Optional[str] = None) -> str:
    """
    Create a simplified fallback prompt when standard parsing fails.

    Args:
        tty_message: The raw TTY message to parse
        error_details: Optional details about why previous parsing failed

    Returns:
        str: The formatted fallback prompt
    """
    error_context = ""
    if error_details:
        error_context = f"\nPrevious parsing attempt failed with: {error_details}. Please try a simpler approach."

    prompt = f"""
    You are SkyReader, a specialized parser for aviation TTY messages. 
    This is a fallback prompt for a message that was difficult to parse.{error_context}
    
    Try to extract the most basic information from this TTY message:
    
    ```
    {tty_message}
    ```
    
    Focus only on these key fields:
    1. Message type (MVT, MVA, or DIV)
    2. Flight number (e.g., QFA8666)
    3. Aircraft registration (e.g., VHZNM)
    4. Airport code (e.g., YPGV)
    
    Return a simple JSON object with just these fields. If you cannot confidently determine a field, use null for its value.
    """
    return prompt


def create_few_shot_parsing_prompt(tty_message: str, few_shot_examples: List[Dict]) -> str:
    """
    Create a prompt that includes few-shot examples for better parsing accuracy.

    Args:
        tty_message: The raw TTY message to parse
        few_shot_examples: List of example dictionaries, each containing 'message' and 'parsed_json'

    Returns:
        str: The formatted prompt with few-shot examples
    """
    # Build examples section
    examples_text = ""
    for i, example in enumerate(few_shot_examples):
        examples_text += f"\nExample {i+1}:\nInput:\n```\n{example['message']}\n```\n\nOutput:\n```json\n{json.dumps(example['parsed_json'], indent=2)}\n```\n"

    prompt = f"""
    You are SkyReader, a specialized parser for aviation TTY messages used by Qantas airline.
    I'll provide you with examples of TTY messages and how they should be parsed into JSON,
    followed by a new message for you to parse.

    {examples_text}
    
    Now, parse the following TTY message using the same format as in the examples:
    
    Input:
    ```
    {tty_message}
    ```
    
    Output:
    ```json
    """

    return prompt