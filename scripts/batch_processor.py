#!/usr/bin/env python
"""
Batch processor script for processing large numbers of TTY messages.
Can be run as a standalone script or as a Docker service.
"""
import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

import httpx

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("batch_processing.log")
    ]
)
logger = logging.getLogger("batch_processor")

# Default settings
DEFAULT_API_URL = "http://api:8000"
DEFAULT_SAMPLES_DIR = "data/samples"
DEFAULT_OUTPUT_DIR = "data/results"
DEFAULT_BATCH_SIZE = 10
DEFAULT_REQUEST_TIMEOUT = 60.0


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Process TTY messages in batch")
    parser.add_argument(
        "--api-url",
        default=os.environ.get("API_URL", DEFAULT_API_URL),
        help="API URL for SkyReader service"
    )
    parser.add_argument(
        "--samples-dir",
        default=os.environ.get("SAMPLES_DIR", DEFAULT_SAMPLES_DIR),
        help="Directory containing TTY message samples"
    )
    parser.add_argument(
        "--output-dir",
        default=os.environ.get("OUTPUT_DIR", DEFAULT_OUTPUT_DIR),
        help="Directory for output results"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=int(os.environ.get("BATCH_SIZE", DEFAULT_BATCH_SIZE)),
        help="Number of messages to process in each batch"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.environ.get("REQUEST_TIMEOUT", DEFAULT_REQUEST_TIMEOUT)),
        help="API request timeout in seconds"
    )
    return parser.parse_args()


def read_tty_files(directory: str) -> List[Dict[str, str]]:
    """
    Read all TTY message files from a directory.

    Args:
        directory: Directory containing TTY message files

    Returns:
        List[Dict[str, str]]: List of messages with their IDs
    """
    messages = []
    dir_path = Path(directory)

    # Create directory if it doesn't exist
    dir_path.mkdir(parents=True, exist_ok=True)

    # Look for .tty files
    tty_files = list(dir_path.glob("*.tty"))

    if not tty_files:
        logger.warning(f"No TTY files found in {directory}")
        return messages

    logger.info(f"Found {len(tty_files)} TTY files in {directory}")

    # Read each file
    for file_path in tty_files:
        try:
            with open(file_path, "r") as f:
                content = f.read().strip()

                # Add to messages list
                messages.append({
                    "message": content,
                    "message_id": file_path.stem
                })
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")

    return messages


def process_batch(
        messages: List[Dict[str, str]],
        api_url: str,
        timeout: float
) -> Dict[str, Any]:
    """
    Process a batch of TTY messages.

    Args:
        messages: List of messages to process
        api_url: API URL for SkyReader service
        timeout: API request timeout in seconds

    Returns:
        Dict[str, Any]: API response data
    """
    batch_endpoint = f"{api_url}/batch_parse"

    try:
        # Make API request
        response = httpx.post(
            batch_endpoint,
            json={"messages": messages},
            timeout=timeout
        )

        # Check response
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API error: {response.status_code} - {response.text}")
            return {
                "error": f"API error: {response.status_code}",
                "detail": response.text
            }

    except Exception as e:
        logger.error(f"Error processing batch: {str(e)}")
        return {
            "error": "Processing error",
            "detail": str(e)
        }


def save_results(results: Dict[str, Any], output_dir: str, batch_num: int) -> str:
    """
    Save batch processing results to a file.

    Args:
        results: Batch processing results
        output_dir: Directory for output files
        batch_num: Batch number

    Returns:
        str: Path to the output file
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Create timestamp
    timestamp = time.strftime("%Y%m%d-%H%M%S")

    # Create output filename
    filename = f"batch_{batch_num}_{timestamp}.json"
    file_path = output_path / filename

    # Save results
    with open(file_path, "w") as f:
        json.dump(results, f, indent=2)

    return str(file_path)


def main():
    """Main function."""
    # Parse arguments
    args = parse_arguments()

    # Read TTY messages
    messages = read_tty_files(args.samples_dir)

    if not messages:
        logger.error("No messages to process")
        return 1

    logger.info(f"Processing {len(messages)} messages in batches of {args.batch_size}")

    # Split into batches
    batches = [
        messages[i:i + args.batch_size]
        for i in range(0, len(messages), args.batch_size)
    ]

    # Process each batch
    total_successful = 0
    total_failed = 0

    for i, batch in enumerate(batches):
        logger.info(f"Processing batch {i+1}/{len(batches)} ({len(batch)} messages)")

        # Process batch
        start_time = time.time()
        results = process_batch(batch, args.api_url, args.timeout)
        processing_time = time.time() - start_time

        # Save results
        if "error" not in results:
            file_path = save_results(results, args.output_dir, i+1)

            # Update counters
            total_successful += results.get("successful_count", 0)
            total_failed += results.get("failed_count", 0)

            # Log results
            logger.info(
                f"Batch {i+1} completed in {processing_time:.2f}s: "
                f"{results.get('successful_count', 0)} successful, "
                f"{results.get('failed_count', 0)} failed, "
                f"saved to {file_path}"
            )
        else:
            # Log error
            logger.error(f"Batch {i+1} failed: {results.get('error')}")
            total_failed += len(batch)

        # Brief pause between batches
        time.sleep(1)

    # Log final results
    logger.info(
        f"Processing complete: {total_successful} successful, {total_failed} failed"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())