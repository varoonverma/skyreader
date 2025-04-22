"""
Message handling service for the SkyReader TTY Message Parser.
"""
import time
import uuid
from typing import Dict, List, Any, Optional, Tuple

from app.core.logging import get_logger
from app.services.parser_service import parse_tty_message, batch_parse_tty_messages
from app.schemas.message import ParsedTTYMessage
from app.utils.message_validator import validate_tty_message, detect_message_type


# Configure logger
logger = get_logger(__name__)


class MessageService:
    """Service for handling TTY messages."""

    @staticmethod
    def generate_message_id() -> str:
        """
        Generate a unique message ID.

        Returns:
            str: A unique message ID
        """
        return str(uuid.uuid4())

    @staticmethod
    def preprocess_message(message: str) -> str:
        """
        Preprocess a TTY message before parsing.
        This can include normalizing whitespace, etc.

        Args:
            message: The raw TTY message

        Returns:
            str: The preprocessed message
        """
        # Normalize line endings
        message = message.replace('\r\n', '\n').replace('\r', '\n')

        # Remove leading/trailing whitespace
        message = message.strip()

        return message

    @staticmethod
    async def process_message(
            message: str,
            message_id: Optional[str] = None
    ) -> Tuple[ParsedTTYMessage, float, str]:
        """
        Process a single TTY message.

        Args:
            message: The raw TTY message
            message_id: Optional message identifier

        Returns:
            Tuple containing parsed message, processing time, and parsing method
        """
        # Generate message ID if not provided
        if not message_id:
            message_id = MessageService.generate_message_id()

        # Preprocess message
        preprocessed_message = MessageService.preprocess_message(message)

        # Validate message
        if not validate_tty_message(preprocessed_message):
            raise ValueError(f"Invalid TTY message format: {message_id}")

        # Parse message
        return parse_tty_message(preprocessed_message, message_id)

    @staticmethod
    async def process_batch(
            messages: List[Tuple[str, Optional[str]]],
            batch_size: int = 10
    ) -> List[Tuple[ParsedTTYMessage, float, str, str]]:
        """
        Process a batch of TTY messages.

        Args:
            messages: List of tuples containing (message, message_id)
            batch_size: Maximum number of messages to process at once

        Returns:
            List of tuples containing (parsed_message, processing_time, parsing_method, message_id)
        """
        # Preprocess all messages
        preprocessed_messages = []
        for message, message_id in messages:
            # Generate message ID if not provided
            if not message_id:
                message_id = MessageService.generate_message_id()

            # Preprocess message
            preprocessed_message = MessageService.preprocess_message(message)

            # Add to list
            preprocessed_messages.append((preprocessed_message, message_id))

        # Process in batches
        results = []
        for i in range(0, len(preprocessed_messages), batch_size):
            batch = preprocessed_messages[i:i+batch_size]

            # Process batch
            batch_results = batch_parse_tty_messages(batch)
            results.extend(batch_results)

        return results

    @staticmethod
    def categorize_messages(
            messages: List[str]
    ) -> Dict[str, List[str]]:
        """
        Categorize TTY messages by their type.

        Args:
            messages: List of raw TTY messages

        Returns:
            Dict mapping message types to lists of messages
        """
        categorized = {
            "MVT": [],
            "MVA": [],
            "DIV": [],
            "UNKNOWN": []
        }

        for message in messages:
            message_type = detect_message_type(message)
            if message_type in categorized:
                categorized[message_type].append(message)
            else:
                categorized["UNKNOWN"].append(message)

        return categorized

    @staticmethod
    def extract_stats_from_batch(
            results: List[Tuple[ParsedTTYMessage, float, str, Optional[str]]]
    ) -> Dict[str, Any]:
        """
        Extract statistics from a batch of parsing results.

        Args:
            results: List of parsing results

        Returns:
            Dict of statistics
        """
        if not results:
            return {
                "message_count": 0,
                "avg_processing_time_ms": 0,
                "message_types": {},
                "parsing_methods": {}
            }

        # Calculate statistics
        total_time = sum(result[1] for result in results)
        avg_time = total_time / len(results)

        # Count message types
        message_types = {}
        for result in results:
            msg_type = result[0].message_type
            message_types[msg_type] = message_types.get(msg_type, 0) + 1

        # Count parsing methods
        parsing_methods = {}
        for result in results:
            method = result[2]
            parsing_methods[method] = parsing_methods.get(method, 0) + 1

        # Calculate average confidence
        avg_confidence = sum(
            result[0].confidence_score or 0.0 for result in results
        ) / len(results)

        return {
            "message_count": len(results),
            "avg_processing_time_ms": avg_time,
            "message_types": message_types,
            "parsing_methods": parsing_methods,
            "avg_confidence": avg_confidence
        }