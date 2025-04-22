"""
Parser service for the SkyReader TTY Message Parser.
"""
import json
import time
from typing import Dict, List, Any, Tuple, Optional

from openai import OpenAI
from openai.types.chat import ChatCompletion

from app.core.config import get_settings
from app.core.logging import get_logger, log_processing_result
from app.schemas.message import ParsedTTYMessage, FlightIdentifier
from app.data.examples import load_few_shot_examples
from app.utils.prompt_builder import create_few_shot_parsing_prompt
from app.utils.prompt_builder import (
    create_parsing_prompt,
    create_detailed_parsing_prompt,
    create_fallback_prompt
)
from app.utils.message_validator import (
    validate_tty_message,
    detect_message_type,
    extract_basic_fields,
    validate_parsed_fields
)


# Configure logger
logger = get_logger(__name__)

# Initialize settings
settings = get_settings()

# Initialize OpenAI client
client = OpenAI(api_key=settings.openai_api_key)


def parse_tty_message(
        message: str,
        message_id: Optional[str] = None,
        use_few_shot: bool = True,
        use_detailed_prompt: bool = False
) -> Tuple[ParsedTTYMessage, float, str]:
    """
    Parse a TTY message using the OpenAI API.

    Args:
        message: The raw TTY message to parse
        message_id: Optional identifier for the message
        use_detailed_prompt: Whether to use a more detailed prompt for difficult cases

    Returns:
        Tuple containing:
        - ParsedTTYMessage: The parsed TTY message data
        - float: Processing time in milliseconds
        - str: Parsing method used ('llm', 'antlr', 'fallback')
    """
    start_time = time.time()
    parsing_method = "llm-few-shot" if use_few_shot else "llm"

    # Validate message format
    if not validate_tty_message(message):
        raise ValueError(f"Invalid TTY message format: {message_id or 'unknown'}")

    try:
        if use_few_shot:
            examples = load_few_shot_examples()
            prompt = create_few_shot_parsing_prompt(message, examples)
            logger.info(f"Using few-shot prompt with {len(examples)} examples")
        else:
            # Use the existing prompt building method
            message_type = detect_message_type(message)
            prompt = create_parsing_prompt(message, message_type)

            logger.info(f"Prompt length: {len(prompt)}")
        # Call the OpenAI API
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are SkyReader, a specialized TTY message parser for aviation."},
                {"role": "user", "content": prompt}
            ],
            temperature=settings.openai_temperature,
            max_tokens=settings.openai_max_tokens
        )

        logger.info(f"OpenAI response status: {response.choices[0].finish_reason}")
        # Process the response
        parsed_result = _process_llm_response(response, message)

        # Validate the parsed fields
        # is_valid, error_message = validate_parsed_fields(parsed_result)
        #
        # if not is_valid:
        #     logger.warning(f"Validation failed for message {message_id}: {error_message}")
        #
        #     if use_detailed_prompt:
        #         # If we already tried the detailed prompt, try the fallback
        #         return _fallback_parsing(message, message_id, error_message, start_time)
        #     else:
        #         # Try again with a more detailed prompt
        #         logger.info(f"Retrying message {message_id} with detailed prompt")
        #         return parse_tty_message(message, message_id, use_few_shot, use_detailed_prompt=True)

        # Create the flight identifier object
        flight_id = FlightIdentifier(
            designator=parsed_result["flight_identifier"]["designator"],
            flight_number=parsed_result["flight_identifier"]["flight_number"],
            scheduled_date=parsed_result["flight_identifier"].get("scheduled_date")
        )

        # Create the parsed TTY message object
        parsed_message = ParsedTTYMessage(
            message_type=parsed_result["message_type"],
            flight_identifier=flight_id,
            aircraft_registration=parsed_result["aircraft_registration"],
            airport_of_movement=parsed_result["airport_of_movement"],
            message_specific_data=parsed_result["message_specific_data"],
            supplementary_info=parsed_result.get("supplementary_info"),
            raw_message=message,
            confidence_score=parsed_result.get("confidence_score", 1.0)
        )

        # Check if confidence is too low and fallback is enabled
        if (parsed_message.confidence_score < settings.confidence_threshold and
                settings.fallback_to_antlr):
            try:
                # Try ANTLR fallback if enabled
                antlr_result, antlr_time = parse_with_antlr(message)
                parsing_method = "antlr"

                # Convert ANTLR result to our schema
                parsed_message = _convert_antlr_to_schema(antlr_result, message)

                logger.info(f"Used ANTLR fallback for message {message_id}")
            except Exception as antlr_error:
                logger.error(f"ANTLR fallback failed for {message_id}: {str(antlr_error)}")
                # Keep the LLM result if ANTLR fails

    except json.JSONDecodeError as json_error:
        logger.error(f"Failed to parse JSON from LLM response for {message_id}: {str(json_error)}")
        return _fallback_parsing(message, message_id, str(json_error), start_time)

    except Exception as e:
        logger.error(f"Error parsing TTY message {message_id}: {str(e)}")
        raise

    processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds

    # Log the result
    success = True
    log_processing_result(message_id or "unknown", processing_time, parsing_method, success, logger)

    return parsed_result, processing_time, parsing_method

def _process_llm_response(response: ChatCompletion, original_message: str) -> Dict[str, Any]:
    """
    Process the LLM response to extract the parsed data.

    Args:
        response: The LLM response
        original_message: The original TTY message

    Returns:
        Dict[str, Any]: The parsed TTY message data
    """
    # Extract the content from the response
    content = response.choices[0].message.content

    # Print the full content for debugging
    print("FULL RESPONSE CONTENT:")
    print(content)

    # Try to find JSON in the response
    json_start = content.find('{')
    json_end = content.rfind('}') + 1

    if json_start >= 0 and json_end > json_start:
        json_content = content[json_start:json_end]
        try:
            parsed_json = json.loads(json_content)
            logger.info(f"Successfully parsed JSON from response")
            print(json.dumps(parsed_json, indent=2))
            # Add the raw message
            if "raw_message" not in parsed_json:
                parsed_json["raw_message"] = original_message

            # Add confidence score
            finish_reason = response.choices[0].finish_reason
            parsed_json["confidence_score"] = 1.0 if finish_reason == "stop" else 0.7

            return parsed_json
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}, content: {json_content[:100]}...")
            raise
    else:
        logger.error(f"No JSON found in response: {content[:100]}...")
        raise ValueError("No JSON found in LLM response")

    # Calculate confidence score based on response metadata
    finish_reason = response.choices[0].finish_reason
    confidence_score = 1.0 if finish_reason == "stop" else 0.7

    # Add confidence score to the parsed data
    parsed_json["confidence_score"] = confidence_score

    # Ensure raw message is included
    parsed_json["raw_message"] = original_message

    return parsed_json


def _fallback_parsing(
        message: str,
        message_id: Optional[str],
        error_details: str,
        start_time: float
) -> Tuple[ParsedTTYMessage, float, str]:
    """
    Fallback parsing method when standard LLM parsing fails.

    Args:
        message: The raw TTY message
        message_id: Optional message identifier
        error_details: Details about why the standard parsing failed
        start_time: The start time for performance measurement

    Returns:
        Tuple containing parsed message, processing time, and parsing method
    """
    logger.info(f"Using fallback parsing for message {message_id}")
    parsing_method = "fallback"

    try:
        # First try using simplified regex-based extraction
        basic_fields = extract_basic_fields(message)

        # If that doesn't work well enough, try a simplified LLM prompt
        if not basic_fields.get("message_type") or not basic_fields.get("flight_identifier"):
            try:
                # Create a simplified fallback prompt
                fallback_prompt = create_fallback_prompt(message, error_details)

                # Call the OpenAI API with simplified expectations
                response = client.chat.completions.create(
                    model=settings.openai_model,
                    messages=[
                        {"role": "system", "content": "You are a TTY message analyzer focusing on key fields only."},
                        {"role": "user", "content": fallback_prompt}
                    ],
                    temperature=0.2,  # Lower temperature for more deterministic results
                    max_tokens=500
                )

                # Extract the content
                content = response.choices[0].message.content

                # Try to find JSON in the response
                json_start = content.find('{')
                json_end = content.rfind('}') + 1

                if json_start >= 0 and json_end > json_start:
                    fallback_json = json.loads(content[json_start:json_end])

                    # Merge with basic fields, preferring fallback results
                    for key, value in fallback_json.items():
                        if value is not None:  # Only override if not None
                            basic_fields[key] = value

            except Exception as fallback_error:
                logger.error(f"Fallback LLM parsing failed: {str(fallback_error)}")
                # Continue with what we got from regex extraction

        # Ensure we have all required fields with defaults if necessary
        if "message_type" not in basic_fields:
            basic_fields["message_type"] = "MVT"  # Default to MVT if unknown

        if "flight_identifier" not in basic_fields:
            basic_fields["flight_identifier"] = {
                "designator": "XXX",
                "flight_number": "0000",
                "scheduled_date": None
            }

        if "aircraft_registration" not in basic_fields:
            basic_fields["aircraft_registration"] = "UNKNOWN"

        if "airport_of_movement" not in basic_fields:
            basic_fields["airport_of_movement"] = "XXX"

        if "message_specific_data" not in basic_fields:
            basic_fields["message_specific_data"] = {}

        # Create flight identifier
        flight_id = FlightIdentifier(
            designator=basic_fields["flight_identifier"]["designator"],
            flight_number=basic_fields["flight_identifier"]["flight_number"],
            scheduled_date=basic_fields["flight_identifier"].get("scheduled_date")
        )

        # Create parsed message with low confidence score
        parsed_message = ParsedTTYMessage(
            message_type=basic_fields["message_type"],
            flight_identifier=flight_id,
            aircraft_registration=basic_fields["aircraft_registration"],
            airport_of_movement=basic_fields["airport_of_movement"],
            message_specific_data=basic_fields["message_specific_data"],
            supplementary_info=None,
            raw_message=message,
            confidence_score=0.5  # Low confidence for fallback parsing
        )

    except Exception as e:
        logger.error(f"Fallback parsing failed for {message_id}: {str(e)}")
        raise ValueError(f"Failed to parse TTY message after multiple attempts: {message_id or 'unknown'}")

    processing_time = (time.time() - start_time) * 1000

    # Log the result
    success = True
    log_processing_result(message_id or "unknown", processing_time, parsing_method, success, logger)

    return parsed_message, processing_time, parsing_method


def parse_with_antlr(message: str) -> Tuple[Dict[str, Any], float]:
    """
    Parse a TTY message using the ANTLR parser.
    This is a placeholder for integration with an existing ANTLR parser.

    Args:
        message: The raw TTY message to parse

    Returns:
        Tuple[Dict[str, Any], float]: The parsed message as a dictionary and processing time
    """
    # This is a placeholder - implement your ANTLR parser integration here
    logger.warning("ANTLR parser not implemented, raising exception")
    raise NotImplementedError("ANTLR parser integration not implemented")


def _convert_antlr_to_schema(antlr_result: Dict[str, Any], original_message: str) -> ParsedTTYMessage:
    """
    Convert ANTLR parsing result to our schema.
    This is a placeholder for ANTLR result conversion.

    Args:
        antlr_result: The result from the ANTLR parser
        original_message: The original TTY message

    Returns:
        ParsedTTYMessage: The converted message in our schema
    """
    # This is a placeholder - implement conversion from your ANTLR output to our schema
    raise NotImplementedError("ANTLR conversion not implemented")


def batch_parse_tty_messages(
        messages: List[Tuple[str, Optional[str]]]
) -> List[Tuple[ParsedTTYMessage, float, str, Optional[str]]]:
    """
    Parse multiple TTY messages in batch.

    Args:
        messages: List of tuples containing (message, message_id)

    Returns:
        List of tuples containing (parsed_message, processing_time, parsing_method, message_id)
    """
    results = []

    for message, message_id in messages:
        try:
            parsed_message, processing_time, parsing_method = parse_tty_message(message, message_id)
            results.append((parsed_message, processing_time, parsing_method, message_id))
        except Exception as e:
            logger.error(f"Error parsing message {message_id}: {str(e)}")
            # For batch processing, we don't want to fail the entire batch if one message fails
            # Instead, we'll log the error and continue with the next message
            continue

    return results